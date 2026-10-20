package __BASE_PACKAGE__.domain.session.data.datasource

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.session.data.datasource.model.StoredTokens
import com.ribads.synapse.core.sharedpref.SharedPrefManager
import com.ribads.synapse.core.sharedpref.getStringOrNull
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json

internal class TokenStore(
    private val storage: SharedPrefManager,
    private val logger: ErrorLogger,
) {

    private val cached by lazy { MutableStateFlow(read()) }

    val tokens: StateFlow<StoredTokens?> by lazy { cached.asStateFlow() }

    suspend fun write(tokens: StoredTokens): Result<Boolean> {
        cached.value = tokens
        return storage.awaitPut(KEY, Json.encodeToString(StoredTokens.serializer(), tokens))
    }

    suspend fun clear(): Result<Boolean> {
        cached.value = null
        return storage.awaitRemove(KEY)
    }

    private fun read(): StoredTokens? {
        val encoded = storage.getStringOrNull(KEY) ?: return null
        return runCatching { Json.decodeFromString(StoredTokens.serializer(), encoded) }
            .onFailure(logger::log)
            .getOrNull()
    }

    private companion object {
        const val KEY = "session_tokens"
    }
}
