package dev.composer.rules

import dev.detekt.api.Config
import dev.detekt.api.Entity
import dev.detekt.api.Finding
import dev.detekt.api.RequiresAnalysisApi
import dev.detekt.api.Rule
import dev.detekt.api.RuleName
import dev.detekt.api.RuleSet
import dev.detekt.api.RuleSetId
import dev.detekt.api.RuleSetProvider
import dev.detekt.api.config
import org.jetbrains.kotlin.analysis.api.analyze
import org.jetbrains.kotlin.analysis.api.components.expressionType
import org.jetbrains.kotlin.analysis.api.components.expectedType
import org.jetbrains.kotlin.analysis.api.components.functionType
import org.jetbrains.kotlin.analysis.api.components.resolveToCall
import org.jetbrains.kotlin.analysis.api.components.resolveToSymbol
import org.jetbrains.kotlin.analysis.api.resolution.successfulFunctionCallOrNull
import org.jetbrains.kotlin.analysis.api.resolution.symbol
import org.jetbrains.kotlin.analysis.api.symbols.symbol
import org.jetbrains.kotlin.analysis.api.symbols.KaConstructorSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaNamedClassSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaPropertySymbol
import org.jetbrains.kotlin.idea.references.mainReference
import org.jetbrains.kotlin.analysis.api.types.KaClassType
import org.jetbrains.kotlin.analysis.api.types.KaFunctionType
import org.jetbrains.kotlin.lexer.KotlinLexer
import org.jetbrains.kotlin.lexer.KtTokens
import org.jetbrains.kotlin.psi.*
import org.jetbrains.kotlin.psi.psiUtil.collectDescendantsOfType

/** Only statically observable contracts. No business-state or rendering verdicts. */
class ComposerRuleSetProvider : RuleSetProvider {
    override val ruleSetId = RuleSetId("Composer")
    override fun instance() = RuleSet(ruleSetId, mapOf(
        RuleName("UntypedEventCallback") to ::UntypedEventCallback,
        RuleName("DroppedEventCallback") to ::DroppedEventCallback,
        RuleName("DroppedUiInput") to ::DroppedUiInput,
        RuleName("UnusedEventCallback") to ::UnusedEventCallback,
        RuleName("UnusedUiParameter") to ::UnusedUiParameter,
        RuleName("StateWriteInComposition") to ::StateWriteInComposition,
        RuleName("CoroutineLaunchInComposition") to ::CoroutineLaunchInComposition,
        RuleName("InvalidLayoutBounds") to ::InvalidLayoutBounds,
        RuleName("WhitespaceLayoutSpacer") to ::WhitespaceLayoutSpacer,
        RuleName("PreviewDuplicateBody") to ::PreviewDuplicateBody,
        RuleName("ConstantLazyItemKey") to ::ConstantLazyItemKey,
        RuleName("UnkeyedRememberCapture") to ::UnkeyedRememberCapture,

        RuleName("NondeterministicDefault") to ::NondeterministicDefault,
        RuleName("NoOpActionDefault") to ::NoOpActionDefault,
        RuleName("PositionalBooleanArguments") to ::PositionalBooleanArguments,
        RuleName("RedundantSizeModifier") to ::RedundantSizeModifier,
        RuleName("BlockingCallInComposition") to ::BlockingCallInComposition,
        RuleName("NondeterministicPreview") to ::NondeterministicPreview,
        RuleName("PreviewEnvironmentDependency") to ::PreviewEnvironmentDependency,
    ))
}

private const val COMPOSABLE = "androidx.compose.runtime.Composable"
private const val PREVIEW = "androidx.compose.ui.tooling.preview.Preview"

// Resolution errors propagate to detekt: never turn a failed typed analysis into a clean scan.
private fun KtNamedFunction.hasAnnotation(fqName: String): Boolean = analyze(this) {
    this@hasAnnotation.symbol.annotations.any { it.classId?.asSingleFqName()?.asString() == fqName }
}

private fun KtCallExpression.callId(): String? = analyze(this) {
    this@callId.resolveToCall()?.successfulFunctionCallOrNull()?.symbol?.callableId?.asSingleFqName()?.asString()
}

private fun KtParameter.className(): String? = analyze(this) {
    (this@className.symbol.returnType as? KaClassType)?.classId?.asSingleFqName()?.asString()
}

private fun KtCallExpression.argumentsByName(): List<Pair<KtExpression, String>> = analyze(this) {
    this@argumentsByName.resolveToCall()?.successfulFunctionCallOrNull()?.valueArgumentMapping
        ?.map { (expression, signature) -> expression to signature.symbol.name.asString() }.orEmpty()
}

private fun KtCallExpression.sourceFunction(): KtNamedFunction? = analyze(this) {
    this@sourceFunction.resolveToCall()?.successfulFunctionCallOrNull()?.symbol?.psi as? KtNamedFunction
}

private fun KtLambdaExpression.synchronousOwner(): KtCallExpression? {
    var node = parent
    while (node is KtValueArgument || node is KtValueArgumentList || node is KtParenthesizedExpression) node = node.parent
    val call = node as? KtCallExpression ?: return null
    val id = call.callId()
    val name = call.argumentsByName().firstOrNull { it.first.unwrapped() == this }?.second
    return call.takeIf {
        id == "androidx.compose.runtime.remember" && name == "calculation" ||
            id in setOf("kotlin.run", "kotlin.let", "kotlin.also", "kotlin.apply", "kotlin.with") && name == "block"
    }
}

private fun KtElement.compositionScope(): Boolean {
    var owner = parent
    while (owner != null) {
        when (owner) {
            is KtNamedFunction -> return owner.hasAnnotation(COMPOSABLE)
            is KtLambdaExpression -> {
                val lambda = owner
                val isComposable = analyze(lambda) {
                    lambda.functionLiteral.functionType.annotations.any {
                        it.classId?.asSingleFqName()?.asString() == COMPOSABLE
                    } || lambda.expectedType?.annotations?.any {
                        it.classId?.asSingleFqName()?.asString() == COMPOSABLE
                    } == true
                }
                if (isComposable) return true
                val synchronous = lambda.synchronousOwner() ?: return false
                owner = synchronous.parent
                continue
            }
            is KtClassOrObject -> return false
        }
        owner = owner.parent
    }
    return false
}

private fun KtCallExpression.directPreview(): Boolean {
    var owner = parent
    while (owner != null) {
        when (owner) {
            is KtNamedFunction -> return owner.hasAnnotation(PREVIEW)
            is KtLambdaExpression, is KtClassOrObject -> return false
        }
        owner = owner.parent
    }
    return false
}

private val nondeterministicCalls = setOf(
    "java.lang.System.currentTimeMillis", "java.lang.System.nanoTime", "java.lang.Math.random",
    "java.util.UUID.randomUUID", "kotlin.random.Random.nextInt", "kotlin.random.Random.nextLong",
    "kotlin.random.Random.nextDouble", "kotlin.random.Random.Default.nextInt",
    "kotlin.random.Random.Default.nextLong", "kotlin.random.Random.Default.nextDouble",
)
private val blockingCalls = setOf(
    "java.lang.Thread.sleep", "kotlinx.coroutines.runBlocking", "java.net.URL.openStream",
    "kotlin.io.readText", "kotlin.io.readBytes", "kotlin.io.readLines",
)

private fun KtCallExpression.isNondeterministic(): Boolean {
    val id = callId() ?: return false
    if (id !in nondeterministicCalls) return false
    if (!id.startsWith("kotlin.random.")) return true
    val receiver = (parent as? KtDotQualifiedExpression)?.takeIf { it.selectorExpression == this }?.receiverExpression
    val reference = when (receiver) {
        is KtNameReferenceExpression -> receiver
        is KtDotQualifiedExpression -> receiver.selectorExpression as? KtNameReferenceExpression
        else -> null
    } ?: return id.startsWith("kotlin.random.Random.Default.") && receiver == null
    return analyze(reference) {
        val symbol = reference.mainReference.resolveToSymbol() as? KaNamedClassSymbol
        symbol?.classId?.asSingleFqName()?.asString() in setOf("kotlin.random.Random", "kotlin.random.Random.Default")
    }
}

class UntypedEventCallback(config: Config) : Rule(config,
    "Composable callbacks must expose typed payloads rather than Any."), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.hasAnnotation(COMPOSABLE)) return
        function.valueParameters.forEach { parameter ->
            val untyped = analyze(parameter) {
                (parameter.symbol.returnType as? KaFunctionType)?.parameterTypes?.any {
                    (it as? KaClassType)?.classId?.asSingleFqName()?.asString() == "kotlin.Any"
                } == true
            }
            if (untyped) report(Finding(Entity.from(parameter),
                "Callback exposes an Any payload. Declare the event/payload type or document the external dynamic contract."))
        }
    }
}

class NondeterministicDefault(config: Config) : Rule(config,
    "Time/random defaults in Composable signatures change when the argument is omitted."), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.hasAnnotation(COMPOSABLE) || function.hasAnnotation(PREVIEW)) return
        function.valueParameters.forEach { parameter ->
            val expression = parameter.defaultValue ?: return@forEach
            // A default callback is invoked later; its body is not the default value calculation.
            if (expression is KtLambdaExpression) return@forEach
            val calls = expression.collectDescendantsOfType<KtCallExpression>() + listOfNotNull(expression as? KtCallExpression)
            calls.distinct().filter { call ->
                var node = call.parent
                var nestedLambda = false
                while (node != null && node != parameter) {
                    if (node is KtLambdaExpression) nestedLambda = true
                    node = node.parent
                }
                !nestedLambda && call.isNondeterministic()
            }.forEach { report(Finding(Entity.from(it),
                "Default argument reads time/randomness. Supply an explicit value with the caller's intended lifetime.")) }
        }
    }
}

class NoOpActionDefault(config: Config) : Rule(config,
    "Configured action callbacks must not silently default to an empty lambda."), RequiresAnalysisApi {
    private val actionNames: List<String> by config(listOf("onSubmit", "onConfirm", "onCommit", "onDelete"))
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.hasAnnotation(COMPOSABLE) || function.hasModifier(KtTokens.PRIVATE_KEYWORD)) return
        function.valueParameters.filter { it.name in actionNames }.forEach { parameter ->
            val lambda = parameter.defaultValue as? KtLambdaExpression ?: return@forEach
            val unitCallback = analyze(parameter) {
                val type = parameter.symbol.returnType as? KaFunctionType
                (type?.returnType as? KaClassType)?.classId?.asSingleFqName()?.asString() == "kotlin.Unit"
            }
            if (unitCallback && lambda.bodyExpression?.statements?.isEmpty() == true) {
                report(Finding(Entity.from(parameter),
                    "Configured action ${parameter.name} defaults to no work. Require it or explicitly exempt a genuinely optional action."))
            }
        }
    }
}

class PositionalBooleanArguments(config: Config) : Rule(config,
    "Name supplied Boolean arguments when a Compose call has multiple flag inputs."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        val flags = analyze(expression) {
            val call = expression.resolveToCall()?.successfulFunctionCallOrNull() ?: return@analyze emptyList()
            if (call.symbol.annotations.none { it.classId?.asSingleFqName()?.asString() == COMPOSABLE }) {
                return@analyze emptyList()
            }
            call.valueArgumentMapping.filter { (_, parameter) ->
                (parameter.symbol.returnType as? KaClassType)?.classId?.asSingleFqName()?.asString() == "kotlin.Boolean"
            }.keys.toList()
        }
        if (flags.size < 2) return
        val unnamed = expression.valueArguments.filter { argument ->
            argument.getArgumentName() == null && argument.getArgumentExpression() in flags
        }
        // A scoring identity is separate from the finding location. Resolve the declaration;
        // never merge unrelated overloads or same-named local/member functions by spelling.
        val target = expression.sourceFunction()
        val contractMarker = if (target == null) "" else {
            val location = (target.containingKtFile.virtualFile?.path ?: target.containingKtFile.name) + ":" + target.textOffset
            val identity = java.security.MessageDigest.getInstance("SHA-256").digest(location.toByteArray())
                .joinToString("") { "%02x".format(it) }
            "[composer-boolean-contract:$identity] "
        }
        if (unnamed.isNotEmpty()) report(Finding(Entity.from(expression),
            contractMarker + "This Composable call supplies ${flags.size} Boolean arguments, ${unnamed.size} without names. " +
                "Name the flag arguments to expose their roles; independent flags do not require a wrapper or enum."))
    }
}

class RedundantSizeModifier(config: Config) : Rule(config,
    "Immediately repeated identical constant size modifiers obscure size ownership."), RequiresAnalysisApi {
    override fun visitDotQualifiedExpression(expression: KtDotQualifiedExpression) {
        super.visitDotQualifiedExpression(expression)
        val outer = expression.selectorExpression as? KtCallExpression ?: return
        val inner = (expression.receiverExpression as? KtDotQualifiedExpression)?.selectorExpression as? KtCallExpression ?: return
        val id = outer.callId() ?: return
        if (id !in setOf("size", "width", "height", "requiredSize", "requiredWidth", "requiredHeight")
                .map { "androidx.compose.foundation.layout.$it" } || inner.callId() != id) return
        if ((inner.valueArguments + outer.valueArguments).any { it.getArgumentName() != null }) return
        val left = inner.valueArguments.mapNotNull { constantDp(it.getArgumentExpression()) }
        val right = outer.valueArguments.mapNotNull { constantDp(it.getArgumentExpression()) }
        if (left.isNotEmpty() && left.size == inner.valueArguments.size && right.size == outer.valueArguments.size && left == right) {
            report(Finding(Entity.from(outer), "Consecutive identical constant size modifiers repeat the same allocation contract."))
        }
    }
    private fun constantDp(expression: KtExpression?): String? {
        val qualified = expression as? KtDotQualifiedExpression ?: return null
        if ((qualified.selectorExpression as? KtNameReferenceExpression)?.getReferencedName() != "dp") return null
        val value = qualified.receiverExpression as? KtConstantExpression ?: return null
        val reference = qualified.selectorExpression as KtNameReferenceExpression
        val realDp = analyze(reference) {
            (reference.mainReference.resolveToSymbol() as? KaPropertySymbol)?.callableId?.asSingleFqName()?.asString() == "androidx.compose.ui.unit.dp"
        }
        if (!realDp) return null
        return value.text
    }
}

private fun KtNamedFunction.concreteSource(): Boolean = bodyExpression != null &&
    !hasModifier(KtTokens.OPEN_KEYWORD) && !hasModifier(KtTokens.OVERRIDE_KEYWORD) &&
    !hasModifier(KtTokens.ABSTRACT_KEYWORD) && !hasModifier(KtTokens.EXPECT_KEYWORD)

private fun KtElement.synchronousInside(body: KtExpression): Boolean {
    if (this == body) return true
    var node = parent
    while (node != null && node != body) {
        if (node is KtNamedFunction || node is KtClassOrObject) return false
        if (node is KtLambdaExpression && node.synchronousOwner() == null) return false
        node = node.parent
    }
    return node == body || this == body
}

private fun blockingPath(call: KtCallExpression, depth: Int, seen: Set<KtNamedFunction>): List<KtCallExpression>? {
    if (call.callId() in blockingCalls) return listOf(call)
    if (depth == 0) return null
    val target = call.sourceFunction() ?: return null
    // A composable callee owns its own finding; do not duplicate it at each caller.
    if (!target.concreteSource() || target.hasAnnotation(COMPOSABLE) || target in seen) return null
    val body = target.bodyExpression ?: return null
    if (body is KtLambdaExpression) return null // Returning a callback does not execute its body.
    val children = (body.collectDescendantsOfType<KtCallExpression>() + listOfNotNull(body as? KtCallExpression)).distinct()
    for (child in children.filter { it.synchronousInside(body) }) {
        val path = blockingPath(child, depth - 1, seen + target)
        if (path != null) return listOf(call) + path
    }
    return null
}

class BlockingCallInComposition(config: Config) : Rule(config,
    "Composition must not synchronously block through direct calls or bounded concrete source helpers."), RequiresAnalysisApi {
    private val maxCallDepth: Int by config(3)
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        if (expression.directPreview() || !expression.compositionScope()) return
        val path = blockingPath(expression, maxCallDepth.coerceIn(0, 8), emptySet()) ?: return
        report(Finding(Entity.from(expression), "Blocking composition path: " + path.joinToString(" -> ") {
            (it.callId() ?: "local") + "@" + it.containingKtFile.name + ":" + it.textOffset
        } + ". Move work to the intended asynchronous owner. Unresolved/virtual/deeper paths are not certified."))
    }
}

private fun KtLambdaExpression.isComposableLambda(): Boolean = analyze(this) {
    functionLiteral.functionType.annotations.any { it.classId?.asSingleFqName()?.asString() == COMPOSABLE } ||
        expectedType?.annotations?.any { it.classId?.asSingleFqName()?.asString() == COMPOSABLE } == true
}

private fun KtExpression.previewCalls(): List<KtCallExpression> =
    (collectDescendantsOfType<KtCallExpression>() + listOfNotNull(this as? KtCallExpression)).distinct().filter { call ->
        var node = call.parent
        var executed = true
        while (node != null && node != this && call != this) {
            if (node is KtNamedFunction || node is KtClassOrObject ||
                node is KtLambdaExpression && node.synchronousOwner() == null && !node.isComposableLambda()) {
                executed = false
                break
            }
            node = node.parent
        }
        executed
    }

private fun previewDependencyPath(call: KtCallExpression, depth: Int, seen: Set<KtNamedFunction>,
    predicate: (KtCallExpression) -> Boolean): List<KtCallExpression>? {
    if (predicate(call)) return listOf(call)
    if (depth <= 0) return null
    val target = call.sourceFunction() ?: return null
    if (!target.concreteSource() || target in seen) return null
    val body = target.bodyExpression ?: return null
    if (body is KtLambdaExpression) return null
    for (child in body.previewCalls()) {
        val path = previewDependencyPath(child, depth - 1, seen + target, predicate)
        if (path != null) return listOf(call) + path
    }
    return null
}

abstract class PreviewInputRule(config: Config, private val external: Boolean) : Rule(config,
    "Existing Preview fixtures must not acquire nondeterministic/external inputs on bounded source paths."), RequiresAnalysisApi {
    private val maxCallDepth: Int by config(3)
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.hasAnnotation(PREVIEW)) return
        val body = function.bodyExpression ?: return
        val forbidden = blockingCalls + setOf("java.lang.System.getenv", "androidx.lifecycle.viewmodel.compose.viewModel",
            "androidx.hilt.navigation.compose.hiltViewModel")
        val roots = listOf(body) + function.valueParameters.mapNotNull { it.defaultValue }.filterNot { it is KtLambdaExpression }
        for (call in roots.flatMap { it.previewCalls() }) {
            val path = previewDependencyPath(call, maxCallDepth.coerceIn(0, 8), setOf(function)) {
                if (external) it.callId() in forbidden else it.isNondeterministic()
            } ?: continue
            report(Finding(Entity.from(call), "Preview fixture input path: " + path.joinToString(" -> ") {
                (it.callId() ?: "local") + "@" + it.containingKtFile.name + ":" + it.textOffset
            } + ". Supply fixed sample inputs; deferred, unknown and deeper paths are not certified."))
        }
    }
}
class NondeterministicPreview(config: Config) : PreviewInputRule(config, false)
class PreviewEnvironmentDependency(config: Config) : PreviewInputRule(config, true)

/** Only whitespace-only literal Text arguments: no guesses about dynamic/business strings. */
class WhitespaceLayoutSpacer(config: Config) : Rule(config,
    "Whitespace-only Text is not an explicit layout spacing contract."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        if (!expression.compositionScope() || expression.callId() !in setOf(
            "androidx.compose.material.Text", "androidx.compose.material3.Text", "androidx.compose.foundation.text.BasicText")) return
        val text = expression.argumentsByName().firstOrNull { it.second == "text" }?.first?.unwrapped() as? KtStringTemplateExpression ?: return
        if (text.entries.any { it !is KtLiteralStringTemplateEntry && it !is KtEscapeStringTemplateEntry }) return
        val value = text.entries.joinToString("") { if (it is KtEscapeStringTemplateEntry) it.unescapedValue else it.text }
        if (value.isNotEmpty() && value.all { it == ' ' || it == '\t' || it == '\u00a0' || it == '\u2007' || it == '\u202f' }) {
            report(Finding(Entity.from(text), "Whitespace-only Text reserves glyph-dependent space. Use an explicit layout spacing contract or record an intentional text-metrics exception."))
        }
    }
}

private fun KtExpression.bodyTokens(): List<String> {
    val input = text
    val lexer = KotlinLexer()
    lexer.start(input)
    val tokens = mutableListOf<String>()
    while (lexer.tokenType != null) {
        val type = lexer.tokenType
        if (type.toString() != "WHITE_SPACE" && !KtTokens.COMMENTS.contains(type)) {
            tokens += type.toString() + ":" + input.substring(lexer.tokenStart, lexer.tokenEnd)
        }
        lexer.advance()
    }
    return tokens
}

class PreviewDuplicateBody(config: Config) : Rule(config,
    "An existing Preview should delegate instead of copying a nontrivial production Composable body."), RequiresAnalysisApi {
    private val minBodyTokens: Int by config(40)
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.hasAnnotation(PREVIEW)) return
        val tokens = function.bodyExpression?.bodyTokens() ?: return
        if (tokens.size < minBodyTokens.coerceAtLeast(1)) return
        val duplicate = function.containingKtFile.declarations.filterIsInstance<KtNamedFunction>().firstOrNull { other ->
            other != function && other.hasAnnotation(COMPOSABLE) && !other.hasAnnotation(PREVIEW) && other.bodyExpression?.bodyTokens() == tokens
        } ?: return
        report(Finding(Entity.from(function), "Preview copies the token-identical body of ${duplicate.name} in the same file. Delegate to that component; this check does not certify arbitrary production-path equivalence."))
    }
}

// A reference is matched by resolved symbol, not its spelling (shadowed names do not count).
private fun KtNamedFunction.parameterReferences(parameter: KtParameter): List<KtNameReferenceExpression> {
    val roots = listOfNotNull(bodyExpression) + valueParameters.filter { it != parameter }.mapNotNull { it.defaultValue }
    return roots.flatMap { root -> root.collectDescendantsOfType<KtNameReferenceExpression>() + listOfNotNull(root as? KtNameReferenceExpression) }
        .filter { reference -> analyze(reference) { reference.mainReference.resolveToSymbol() == parameter.symbol } }
}
private fun KtNamedFunction.references(parameter: KtParameter): Boolean = parameterReferences(parameter).isNotEmpty()

private fun KtNamedFunction.inspectableContract(): Boolean =
    bodyExpression != null && !hasModifier(KtTokens.OVERRIDE_KEYWORD) &&
        !hasModifier(KtTokens.EXPECT_KEYWORD) && !hasModifier(KtTokens.ACTUAL_KEYWORD) && hasAnnotation(COMPOSABLE)

class UnusedEventCallback(config: Config) : Rule(config,
    "A declared event callback must be referenced by its implementation."), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.inspectableContract()) return
        function.valueParameters.filter { parameter -> analyze(parameter) {
            parameter.symbol.returnType is KaFunctionType && parameter.name?.matches(Regex("on[A-Z].*")) == true
        } }.filterNot { function.references(it) }.forEach {
            report(Finding(Entity.from(it), "Event callback is never referenced in this implementation. Wire it to its consumer or remove the unsupported contract."))
        }
    }
}

class UnusedUiParameter(config: Config) : Rule(config,
    "Declared UI data inputs must reach an implementation consumer."), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (!function.inspectableContract()) return
        function.valueParameters.filter { parameter -> analyze(parameter) {
            val type = parameter.symbol.returnType
            type !is KaFunctionType && (type as? KaClassType)?.classId?.asSingleFqName()?.asString() != "androidx.compose.ui.Modifier"
        } }.filterNot { function.references(it) }.forEach {
            report(Finding(Entity.from(it), "UI data parameter is never referenced. This check establishes missing consumption, not the meaning of used inputs."))
        }
    }
}

class StateWriteInComposition(config: Config) : Rule(config,
    "Direct snapshot state writes during composition risk feedback and repeated mutation."), RequiresAnalysisApi {
    private fun inspect(target: KtExpression?) {
        if (target == null) return
        val reference = ((target as? KtDotQualifiedExpression)?.selectorExpression as? KtNameReferenceExpression)
            ?: target as? KtNameReferenceExpression ?: return
        if (!target.compositionScope() || freshRememberInitialization(reference)) return
        val delegated = analyze(reference) {
            reference.mainReference.resolveToSymbol()?.psi as? KtProperty
        }?.delegateExpression
        val delegatedState = delegated != null && analyze(delegated) {
            (delegated.expressionType as? KaClassType)?.classId?.asSingleFqName()?.asString() in snapshotStateTypes
        }
        val stateProperty = delegatedState || analyze(reference) {
            val id = (reference.mainReference.resolveToSymbol() as? KaPropertySymbol)?.callableId?.asSingleFqName()?.asString()
            id in setOf("androidx.compose.runtime.MutableState.value", "androidx.compose.runtime.MutableIntState.intValue",
                "androidx.compose.runtime.MutableLongState.longValue", "androidx.compose.runtime.MutableFloatState.floatValue",
                "androidx.compose.runtime.MutableDoubleState.doubleValue")
        }
        if (stateProperty) report(Finding(Entity.from(target), "Snapshot state is written directly in composition. Move the write to the intended event/effect owner."))
    }
    override fun visitBinaryExpression(expression: KtBinaryExpression) {
        super.visitBinaryExpression(expression)
        if (expression.operationToken in setOf(KtTokens.EQ, KtTokens.PLUSEQ, KtTokens.MINUSEQ, KtTokens.MULTEQ, KtTokens.DIVEQ, KtTokens.PERCEQ)) inspect(expression.left)
    }
    override fun visitUnaryExpression(expression: KtUnaryExpression) {
        super.visitUnaryExpression(expression)
        if (expression.operationToken == KtTokens.PLUSPLUS || expression.operationToken == KtTokens.MINUSMINUS) inspect(expression.baseExpression)
    }
}

class CoroutineLaunchInComposition(config: Config) : Rule(config,
    "Coroutine builders must be owned by an event or effect, not directly invoked by composition."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        if (expression.compositionScope() && expression.callId() in setOf("kotlinx.coroutines.launch", "kotlinx.coroutines.async")) {
            report(Finding(Entity.from(expression), "Coroutine starts directly during composition and can restart on recomposition. Use an explicit event/effect lifetime."))
        }
    }
}

private fun KtExpression.unwrapped(): KtExpression = (this as? KtParenthesizedExpression)?.expression?.unwrapped() ?: this
private fun numericDp(expression: KtExpression?): Double? {
    val node = expression?.unwrapped() ?: return null
    if (node is KtPrefixExpression && node.operationToken == KtTokens.MINUS) return numericDp(node.baseExpression)?.let { -it }
    val qualified = node as? KtDotQualifiedExpression ?: return null
    val reference = qualified.selectorExpression as? KtNameReferenceExpression ?: return null
    val realDp = analyze(reference) {
        (reference.mainReference.resolveToSymbol() as? KaPropertySymbol)?.callableId?.asSingleFqName()?.asString() == "androidx.compose.ui.unit.dp"
    }
    if (!realDp) return null
    val value = qualified.receiverExpression.unwrapped()
    if (value !is KtConstantExpression && !(value is KtPrefixExpression && value.operationToken == KtTokens.MINUS && value.baseExpression is KtConstantExpression)) return null
    return value.text.replace("_", "").removeSuffix("f").removeSuffix("F").toDoubleOrNull()
}

class InvalidLayoutBounds(config: Config) : Rule(config,
    "Constant padding must be nonnegative and explicit size ranges must be ordered."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        val id = expression.callId() ?: return
        val prefix = "androidx.compose.foundation.layout."
        if (id == prefix + "padding" || id == prefix + "absolutePadding") {
            expression.valueArguments.filter { (numericDp(it.getArgumentExpression()) ?: 0.0) < 0 }.forEach {
                report(Finding(Entity.from(it), "Negative constant padding violates the Compose padding contract."))
            }
            return
        }
        val names = when (id.removePrefix(prefix).takeIf { id.startsWith(prefix) }) {
            "widthIn", "heightIn", "requiredWidthIn", "requiredHeightIn" -> listOf("min", "max")
            "sizeIn", "requiredSizeIn" -> listOf("minWidth", "minHeight", "maxWidth", "maxHeight")
            else -> return
        }
        val values = expression.valueArguments.mapIndexedNotNull { index, argument ->
            val name = argument.getArgumentName()?.asName?.asString() ?: names.getOrNull(index) ?: return@mapIndexedNotNull null
            numericDp(argument.getArgumentExpression())?.let { name to it }
        }.toMap()
        val pairs = if (names.size == 2) listOf("min" to "max") else listOf("minWidth" to "maxWidth", "minHeight" to "maxHeight")
        if (pairs.any { (low, high) -> values[low] != null && values[high] != null && values.getValue(low) > values.getValue(high) }) {
            report(Finding(Entity.from(expression), "Explicit constant minimum exceeds maximum. Declare an ordered size range."))
        }
    }
}

class ConstantLazyItemKey(config: Config) : Rule(config,
    "Repeated lazy items must not share a literal constant key."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        val id = expression.callId() ?: return
        if (id !in listOf("androidx.compose.foundation.lazy", "androidx.compose.foundation.lazy.grid", "androidx.compose.foundation.lazy.staggeredgrid")
                .flatMap { listOf("$it.items", "$it.itemsIndexed", "$it.LazyListScope.items", "$it.LazyGridScope.items", "$it.LazyStaggeredGridScope.items") }) return
        val key = expression.argumentsByName().firstOrNull { it.second == "key" }?.first?.unwrapped() as? KtLambdaExpression ?: return
        val value = key.bodyExpression?.statements?.singleOrNull()?.unwrapped() ?: return
        if (value.constantKeyExpression()) report(Finding(Entity.from(key), "Constant lazy-item key is duplicated whenever the collection contains multiple items. Use stable item identity or justify a guaranteed singleton."))
    }
}

private val snapshotStateTypes = setOf("androidx.compose.runtime.MutableState", "androidx.compose.runtime.State",
    "androidx.compose.runtime.MutableIntState", "androidx.compose.runtime.MutableLongState",
    "androidx.compose.runtime.MutableFloatState", "androidx.compose.runtime.MutableDoubleState",
    "androidx.compose.runtime.snapshots.SnapshotStateList", "androidx.compose.runtime.snapshots.SnapshotStateMap")

private fun KtNameReferenceExpression.accessPath(): KtExpression {
    var expression: KtExpression = this
    while (true) {
        val parent = expression.parent as? KtDotQualifiedExpression ?: return expression
        if (parent.receiverExpression != expression || parent.selectorExpression !is KtNameReferenceExpression) return expression
        expression = parent
    }
}

class UnkeyedRememberCapture(config: Config) : Rule(config,
    "Remember calculations must account for captured inputs in invalidation keys."), RequiresAnalysisApi {
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        if (expression.callId() != "androidx.compose.runtime.remember") return
        // Spread/aliased key arrays require a separate data-flow proof, not a guessed missing key.
        if (expression.valueArguments.any { it.isSpread }) return
        val mapped = expression.argumentsByName()
        val calculation = mapped.firstOrNull { it.second == "calculation" }?.first?.unwrapped() as? KtLambdaExpression ?: return
        val body = calculation.bodyExpression ?: return
        val last = body.statements.lastOrNull() ?: return
        val stateHolder = analyze(last) { (last.expressionType as? KaClassType)?.classId?.asSingleFqName()?.asString() in snapshotStateTypes }
        if (stateHolder) return // Intentional initial state is not automatically an invalid cache.
        var node = expression.parent
        while (node != null && node !is KtNamedFunction) node = node.parent
        val function = node ?: return
        if (!function.hasAnnotation(COMPOSABLE)) return
        val keys = mapped.filter { it.second != "calculation" }.map { it.first.unwrapped() }
        if (keys.any { it is KtLambdaExpression }) return // Compiler memoization/closure identity is outside this predicate.
        val refs = body.collectDescendantsOfType<KtNameReferenceExpression>()
        val missing = refs.mapNotNull { ref ->
            val parameter = analyze(ref) { function.valueParameters.firstOrNull { it.symbol == ref.mainReference.resolveToSymbol() } } ?: return@mapNotNull null
            val path = ref.accessPath().text.replace(Regex("\\s+"), "")
            val keyed = keys.any { key ->
                key.text.replace(Regex("\\s+"), "") == path || key is KtNameReferenceExpression && analyze(key) { key.mainReference.resolveToSymbol() == parameter.symbol }
            }
            if (keyed) null else path
        }.distinct().sorted()
        if (missing.isNotEmpty()) report(Finding(Entity.from(expression),
            "Remember calculation captures inputs without matching keys: ${missing.joinToString()}. Key the dependency or document intentional initial-only behavior. State-holder initialization is excluded."))
    }
}

private fun KtCallExpression.sourceArguments(): List<Pair<KtExpression, KtParameter>> = analyze(this) {
    this@sourceArguments.resolveToCall()?.successfulFunctionCallOrNull()?.valueArgumentMapping?.mapNotNull { (argument, signature) ->
        (signature.symbol.psi as? KtParameter)?.let { argument to it }
    }.orEmpty()
}

// null means unknown/not proven discarded. Never infer that an external/virtual/deeper path consumes or drops input.
private fun discardedPath(function: KtNamedFunction, parameter: KtParameter, depth: Int, seen: Set<KtParameter>): List<KtParameter>? {
    if (!function.concreteSource() || parameter in seen || depth < 0) return null
    val refs = function.parameterReferences(parameter)
    if (refs.isEmpty()) return listOf(parameter)
    var representative: List<KtParameter>? = null
    for (reference in refs) {
        var node = reference.parent
        while (node is KtParenthesizedExpression) node = node.parent
        val argument = node as? KtValueArgument ?: return null
        val call = argument.parent?.parent as? KtCallExpression ?: return null
        val target = call.sourceFunction() ?: return null
        val mapped = call.sourceArguments().firstOrNull { it.first.unwrapped() == reference }?.second ?: return null
        val child = discardedPath(target, mapped, depth - 1, seen + parameter) ?: return null
        if (representative == null) representative = child
    }
    return representative?.let { listOf(parameter) + it }
}

abstract class DroppedInputRule(config: Config, private val callbacks: Boolean) : Rule(config,
    "A forwarded component input must not terminate in a concrete helper that never consumes it."), RequiresAnalysisApi {
    private val maxCallDepth: Int by config(3)
    override fun visitCallExpression(expression: KtCallExpression) {
        super.visitCallExpression(expression)
        var node = expression.parent
        while (node != null && node !is KtNamedFunction) node = node.parent
        val owner = node ?: return
        if (!owner.inspectableContract()) return
        val target = expression.sourceFunction() ?: return
        // Composable declarations are already owned by UnusedEventCallback/UnusedUiParameter.
        if (target.hasAnnotation(COMPOSABLE)) return
        for ((arg, destination) in expression.sourceArguments()) {
            val reference = arg.unwrapped() as? KtNameReferenceExpression ?: continue
            val source = analyze(reference) { owner.valueParameters.firstOrNull { it.symbol == reference.mainReference.resolveToSymbol() } } ?: continue
            val callback = analyze(source) { source.symbol.returnType is KaFunctionType }
            if (callback != callbacks || source.className() == "androidx.compose.ui.Modifier") continue
            val path = discardedPath(target, destination, maxCallDepth.coerceIn(0, 8) - 1, emptySet()) ?: continue
            val leaf = path.last()
            val location = (leaf.containingKtFile.virtualFile?.path ?: leaf.containingKtFile.name) + ":" + leaf.textOffset
            val defect = java.security.MessageDigest.getInstance("SHA-256").digest(location.toByteArray())
                .joinToString("") { "%02x".format(it) }
            report(Finding(Entity.from(arg), "[composer-discarded:$defect] Forwarded input ${source.name} is discarded along concrete source parameters: " +
                path.joinToString(" -> ") { it.containingKtFile.name + ":" + it.textOffset + "/" + it.name } +
                ". Other references do not repair this specific dropped route; unknown paths remain outside the proof."))
        }
    }
}
class DroppedEventCallback(config: Config) : DroppedInputRule(config, true)
class DroppedUiInput(config: Config) : DroppedInputRule(config, false)

private fun KtExpression.constantKeyExpression(depth: Int = 0): Boolean {
    if (depth > 8) return false
    val value = unwrapped()
    return when (value) {
        is KtConstantExpression -> true
        is KtStringTemplateExpression -> value.entries.all { it is KtLiteralStringTemplateEntry || it is KtEscapeStringTemplateEntry }
        is KtPrefixExpression -> value.operationToken in setOf(KtTokens.PLUS, KtTokens.MINUS, KtTokens.EXCL) && value.baseExpression?.constantKeyExpression(depth + 1) == true
        is KtBinaryExpression -> value.operationToken in setOf(KtTokens.PLUS, KtTokens.MINUS, KtTokens.MUL, KtTokens.DIV, KtTokens.PERC) &&
            value.left?.constantKeyExpression(depth + 1) == true && value.right?.constantKeyExpression(depth + 1) == true
        else -> false
    }
}

// Fresh receiver initialization inside remember is not mutation of a previously observed instance.
// Only exact constructor/state-factory receivers and resolved own-member writes qualify.
private fun freshRememberInitialization(reference: KtNameReferenceExpression): Boolean {
    val qualified = reference.parent as? KtDotQualifiedExpression
    if (qualified?.selectorExpression == reference && qualified.receiverExpression.text != "this") return false
    val ownerClass = analyze(reference) {
        (reference.mainReference.resolveToSymbol() as? KaPropertySymbol)?.callableId?.classId
    } ?: return false
    var node = reference.parent
    var freshApply: KtCallExpression? = null
    while (node != null && node !is KtNamedFunction && node !is KtClassOrObject) {
        if (node is KtLambdaExpression) {
            val call = node.synchronousOwner() ?: return false
            if (call.callId() == "kotlin.apply") {
                val receiver = (call.parent as? KtDotQualifiedExpression)?.receiverExpression?.unwrapped() as? KtCallExpression ?: return false
                val stateFactories = setOf("androidx.compose.runtime.mutableStateOf", "androidx.compose.runtime.mutableIntStateOf",
                    "androidx.compose.runtime.mutableLongStateOf", "androidx.compose.runtime.mutableFloatStateOf", "androidx.compose.runtime.mutableDoubleStateOf")
                val constructor = analyze(receiver) { receiver.resolveToCall()?.successfulFunctionCallOrNull()?.symbol is KaConstructorSymbol }
                val factory = receiver.callId() in stateFactories
                if (!constructor && !factory) return false
                val freshClass = analyze(receiver) { (receiver.expressionType as? KaClassType)?.classId }
                if (freshClass != ownerClass) return false
                if (constructor) {
                    // A fresh wrapper may still delegate to state borrowed from its caller.
                    val property = analyze(reference) { reference.mainReference.resolveToSymbol()?.psi as? KtProperty }
                    val delegate = property?.delegateExpression?.unwrapped() as? KtCallExpression ?: return false
                    if (delegate.callId() !in stateFactories) return false
                }
                freshApply = call
            }
            if (call.callId() == "androidx.compose.runtime.remember") return freshApply != null
            node = call.parent
            continue
        }
        node = node.parent
    }
    return false
}
