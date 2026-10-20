package __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.api.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal data class __DOMAIN_PASCAL__ApiResponse(
    @SerialName("id") val id: String,
    @SerialName("name") val name: String? = null,
)
