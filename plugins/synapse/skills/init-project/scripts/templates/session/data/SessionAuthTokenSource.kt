package __BASE_PACKAGE__.domain.session.data

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.session.data.datasource.TokenRefreshDataSource
import __BASE_PACKAGE__.domain.session.data.datasource.TokenStore
import __BASE_PACKAGE__.domain.session.data.datasource.model.StoredTokens
import com.ribads.synapse.core.network.AuthTokenSource
import com.ribads.synapse.core.network.AuthTokens
import com.ribads.synapse.core.network.NetworkFailure
import com.ribads.synapse.core.network.toNetworkFailure
import kotlin.coroutines.cancellation.CancellationException

internal class SessionAuthTokenSource(
    private val store: TokenStore,
    private val refreshDataSource: TokenRefreshDataSource,
    private val logger: ErrorLogger,
) : AuthTokenSource {

    override suspend fun current(): AuthTokens? = store.tokens.value?.toAuthTokens()

    override suspend fun refresh(stale: AuthTokens): AuthTokens? {
        val refreshToken = stale.refreshToken ?: return endSession()
        val renewed = runCatching { refreshDataSource.refresh(refreshToken) }.getOrElse { failure ->
            if (failure is CancellationException) throw failure
            logger.log(failure)
            if (failure.toNetworkFailure().isRejection()) return endSession()
            throw failure
        }
        store.write(renewed).onFailure(logger::log)
        return renewed.toAuthTokens()
    }

    private suspend fun endSession(): AuthTokens? {
        store.clear().onFailure(logger::log)
        return null
    }

    private fun NetworkFailure.isRejection(): Boolean =
        this == NetworkFailure.Unauthorized || (this is NetworkFailure.Http && status in REJECTED_STATUSES)

    private fun StoredTokens.toAuthTokens() = AuthTokens(accessToken = accessToken, refreshToken = refreshToken)

    private companion object {
        val REJECTED_STATUSES = setOf(400, 403)
    }
}
