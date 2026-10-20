package __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource

import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.api.model.__DOMAIN_PASCAL__ApiResponse
import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.dto.__DOMAIN_PASCAL__Dto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get

internal class __DOMAIN_PASCAL__DataSource(private val client: HttpClient) {

    suspend fun fetch(): List<__DOMAIN_PASCAL__Dto> =
        client.get(PATH).body<List<__DOMAIN_PASCAL__ApiResponse>>().map { it.toDto() }

    private fun __DOMAIN_PASCAL__ApiResponse.toDto() = __DOMAIN_PASCAL__Dto(id = id, name = name.orEmpty())

    private companion object {
        const val PATH = "__DOMAIN__"
    }
}
