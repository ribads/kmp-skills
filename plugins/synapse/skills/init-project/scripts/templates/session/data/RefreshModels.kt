package __BASE_PACKAGE__.domain.session.data.datasource.api.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal data class RefreshRequest(
    @SerialName("refresh_token") val refreshToken: String,
)

@Serializable
internal data class RefreshResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String? = null,
)
