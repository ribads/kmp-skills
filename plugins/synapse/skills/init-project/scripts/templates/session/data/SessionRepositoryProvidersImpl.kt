package __BASE_PACKAGE__.domain.session.data.di

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.session.data.SessionAuthTokenSource
import __BASE_PACKAGE__.domain.session.data.SessionRepositoryImpl
import __BASE_PACKAGE__.domain.session.data.datasource.TokenRefreshDataSource
import __BASE_PACKAGE__.domain.session.data.datasource.TokenStore
import __BASE_PACKAGE__.domain.session.entities.SessionRepository
import __BASE_PACKAGE__.domain.session.entities.di.SessionRepositoryProviders
import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.core.network.AuthTokenSource
import com.ribads.synapse.core.sharedpref.SharedPrefManager
import io.ktor.client.HttpClient
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
@SingletonScope
abstract class SessionRepositoryProvidersImpl(
    private val tokenEndpointClient: HttpClient,
    private val storage: SharedPrefManager,
    private val logger: ErrorLogger,
) : SessionRepositoryProviders {

    abstract val authTokenSource: AuthTokenSource

    @SingletonScope
    @Provides
    internal fun provideTokenStore(): TokenStore = TokenStore(storage, logger)

    @SingletonScope
    @Provides
    internal fun provideSessionRepository(store: TokenStore): SessionRepository = SessionRepositoryImpl(store, logger)

    @SingletonScope
    @Provides
    internal fun provideAuthTokenSource(store: TokenStore): AuthTokenSource =
        SessionAuthTokenSource(store, TokenRefreshDataSource(tokenEndpointClient), logger)
}
