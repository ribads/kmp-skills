package __BASE_PACKAGE__.domain.session.data

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.session.data.datasource.TokenStore
import __BASE_PACKAGE__.domain.session.data.datasource.model.StoredTokens
import __BASE_PACKAGE__.domain.session.entities.SessionRepository
import __BASE_PACKAGE__.domain.session.entities.SessionTokens
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map

internal class SessionRepositoryImpl(
    private val store: TokenStore,
    private val logger: ErrorLogger,
) : SessionRepository {

    override fun observeSignedIn(): Flow<Boolean> = store.tokens.map { it != null }.distinctUntilChanged()

    override suspend fun establish(tokens: SessionTokens) {
        store.write(StoredTokens(tokens.accessToken, tokens.refreshToken)).onFailure(logger::log)
    }

    override suspend fun signOut() {
        store.clear().onFailure(logger::log)
    }
}
