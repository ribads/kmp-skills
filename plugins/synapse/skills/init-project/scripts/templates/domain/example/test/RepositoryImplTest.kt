package __BASE_PACKAGE__.domain.__DOMAIN__.data

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.__DOMAIN_PASCAL__DataSource
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Entity
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__EntityResult
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__FailureReason
import com.ribads.synapse.core.network.NetworkConfig
import com.ribads.synapse.core.network.buildHttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.MockRequestHandler
import io.ktor.client.engine.mock.respond
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import kotlin.coroutines.cancellation.CancellationException
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class __DOMAIN_PASCAL__RepositoryImplTest {

    private class RecordingErrorLogger : ErrorLogger {
        val logged = mutableListOf<Any>()

        override fun log(message: String) {
            logged += message
        }

        override fun log(throwable: Throwable) {
            logged += throwable
        }
    }

    private val logger = RecordingErrorLogger()

    private val jsonHeaders = headersOf(HttpHeaders.ContentType, "application/json")

    private fun repositoryAnswering(handler: MockRequestHandler) = __DOMAIN_PASCAL__RepositoryImpl(
        dataSource = __DOMAIN_PASCAL__DataSource(
            buildHttpClient(MockEngine(handler), NetworkConfig(baseUrl = "https://api.example.test/")),
        ),
        logger = logger,
    )

    @Test
    fun `a successful response becomes Success with mapped entities`() = runTest {
        val repository = repositoryAnswering {
            respond("""[{"id":"1","name":"First"},{"id":"2"}]""", HttpStatusCode.OK, jsonHeaders)
        }

        val expected = __DOMAIN_PASCAL__EntityResult.Success(
            listOf(__DOMAIN_PASCAL__Entity(id = "1", name = "First"), __DOMAIN_PASCAL__Entity(id = "2", name = "")),
        )
        assertEquals(expected, repository.fetch())
    }

    @Test
    fun `an offline failure becomes Connectivity and is logged`() = runTest {
        val repository = repositoryAnswering { throw IOException("unreachable") }

        assertEquals(__DOMAIN_PASCAL__EntityResult.Failure(__DOMAIN_PASCAL__FailureReason.Connectivity), repository.fetch())
        assertEquals(1, logger.logged.size)
    }

    @Test
    fun `a 401 becomes Unauthorized`() = runTest {
        val repository = repositoryAnswering { respond("", HttpStatusCode.Unauthorized) }

        assertEquals(__DOMAIN_PASCAL__EntityResult.Failure(__DOMAIN_PASCAL__FailureReason.Unauthorized), repository.fetch())
    }

    @Test
    fun `a malformed body becomes Unexpected`() = runTest {
        val repository = repositoryAnswering { respond("not json", HttpStatusCode.OK, jsonHeaders) }

        assertEquals(__DOMAIN_PASCAL__EntityResult.Failure(__DOMAIN_PASCAL__FailureReason.Unexpected), repository.fetch())
    }

    @Test
    fun `cancellation is rethrown and nothing is logged`() = runTest {
        val requestStarted = CompletableDeferred<Unit>()
        val repository = repositoryAnswering {
            requestStarted.complete(Unit)
            awaitCancellation()
        }

        val fetch = async { repository.fetch() }
        requestStarted.await()
        fetch.cancel()

        assertFailsWith<CancellationException> { fetch.await() }
        assertTrue(logger.logged.isEmpty())
    }
}
