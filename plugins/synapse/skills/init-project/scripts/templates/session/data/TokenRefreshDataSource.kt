package __BASE_PACKAGE__.domain.session.data.datasource

import __BASE_PACKAGE__.domain.session.data.datasource.api.model.RefreshRequest
import __BASE_PACKAGE__.domain.session.data.datasource.api.model.RefreshResponse
import __BASE_PACKAGE__.domain.session.data.datasource.model.StoredTokens
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType

internal class TokenRefreshDataSource(private val client: HttpClient) {

    suspend fun refresh(refreshToken: String): StoredTokens =
        client.post(PATH) {
            contentType(ContentType.Application.Json)
            setBody(RefreshRequest(refreshToken))
        }.body<RefreshResponse>().let { StoredTokens(it.accessToken, it.refreshToken ?: refreshToken) }

    private companion object {
        const val PATH = "auth/refresh"
    }
}
