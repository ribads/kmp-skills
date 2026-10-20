package __BASE_PACKAGE__.domain.session.data.datasource.model

import kotlinx.serialization.Serializable

@Serializable
internal data class StoredTokens(
    val accessToken: String,
    val refreshToken: String?,
)
