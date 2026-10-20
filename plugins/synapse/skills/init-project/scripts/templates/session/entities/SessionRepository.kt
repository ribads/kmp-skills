package __BASE_PACKAGE__.domain.session.entities

import kotlinx.coroutines.flow.Flow

interface SessionRepository {
    fun observeSignedIn(): Flow<Boolean>
    suspend fun establish(tokens: SessionTokens)
    suspend fun signOut()
}
