package __BASE_PACKAGE__.domain.session.data

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.session.data.datasource.TokenRefreshDataSource
import __BASE_PACKAGE__.domain.session.data.datasource.TokenStore
import __BASE_PACKAGE__.domain.session.data.datasource.model.StoredTokens
import com.ribads.synapse.core.network.AuthTokens
import com.ribads.synapse.core.network.NetworkConfig
import com.ribads.synapse.core.network.buildHttpClient
import com.ribads.synapse.core.sharedpref.SharedPrefManager
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.MockRequestHandler
import io.ktor.client.engine.mock.respond
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull

class SessionAuthTokenSourceTest {

    private class InMemoryPrefs : SharedPrefManager {
        private val values = MutableStateFlow<Map<String, Any>>(emptyMap())

        @Suppress("UNCHECKED_CAST")
        override fun <T : Any> get(key: String, defaultValue: T): T = values.value[key] as? T ?: defaultValue

        override fun <T : Any> put(key: String, value: T): Boolean {
            values.value += key to value
            return true
        }

        override fun remove(key: String): Boolean {
            values.value -= key
            return true
        }

        override fun clear(): Boolean {
            values.value = emptyMap()
            return true
        }

        override fun contains(key: String): Boolean = key in values.value

        @Suppress("UNCHECKED_CAST")
        override fun <T : Any> getAsFlow(key: String, defaultValue: T): Flow<T> =
            values.map { it[key] as? T ?: defaultValue }

        override fun keys(): Set<String> = values.value.keys
    }

    private object SilentLogger : ErrorLogger {
        override fun log(message: String) = Unit
        override fun log(throwable: Throwable) = Unit
    }

    private val signedIn = StoredTokens(accessToken = "first", refreshToken = "refresh")

    private val prefs = InMemoryPrefs()

    private suspend fun signedInStore() = TokenStore(prefs, SilentLogger).apply { write(signedIn) }

    private fun tokenSource(store: TokenStore, handler: MockRequestHandler) = SessionAuthTokenSource(
        store = store,
        refreshDataSource = TokenRefreshDataSource(
            buildHttpClient(MockEngine(handler), NetworkConfig(baseUrl = "https://api.example.test/")),
        ),
        logger = SilentLogger,
    )

    private val stale = AuthTokens(accessToken = "first", refreshToken = "refresh")

    @Test
    fun `a refreshed token is stored before refresh returns`() = runTest {
        val store = signedInStore()
        val source = tokenSource(store) {
            respond(
                """{"access_token":"second","refresh_token":"rotated"}""",
                HttpStatusCode.OK,
                headersOf(HttpHeaders.ContentType, "application/json"),
            )
        }

        val renewed = source.refresh(stale)

        assertEquals(AuthTokens(accessToken = "second", refreshToken = "rotated"), renewed)
        assertEquals(StoredTokens(accessToken = "second", refreshToken = "rotated"), store.tokens.value)
    }

    @Test
    fun `a rejected refresh signs out`() = runTest {
        val store = signedInStore()
        val source = tokenSource(store) { respond("", HttpStatusCode.Unauthorized) }

        assertNull(source.refresh(stale))
        assertFalse(SessionRepositoryImpl(store, SilentLogger).observeSignedIn().first())
    }

    @Test
    fun `an offline refresh keeps the session and rethrows`() = runTest {
        val store = signedInStore()
        val source = tokenSource(store) { throw IOException("unreachable") }

        assertFailsWith<IOException> { source.refresh(stale) }
        assertEquals(signedIn, store.tokens.value)
    }

    @Test
    fun `tokens survive a new store over the same prefs`() = runTest {
        signedInStore()

        assertEquals(signedIn, TokenStore(prefs, SilentLogger).tokens.value)
    }
}
