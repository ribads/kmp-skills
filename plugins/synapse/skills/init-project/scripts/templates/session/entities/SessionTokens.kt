package __BASE_PACKAGE__.domain.session.entities

data class SessionTokens(
    val accessToken: String,
    val refreshToken: String?,
)
