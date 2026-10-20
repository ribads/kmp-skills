package __BASE_PACKAGE__.domain.__DOMAIN__.data.di

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.__DOMAIN__.data.__DOMAIN_PASCAL__RepositoryImpl
import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.__DOMAIN_PASCAL__DataSource
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.di.__DOMAIN_PASCAL__RepositoryProviders
import com.ribads.synapse.core.discopes.SingletonScope
import io.ktor.client.HttpClient
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
@SingletonScope
abstract class __DOMAIN_PASCAL__RepositoryProvidersImpl(
    private val client: HttpClient,
    private val logger: ErrorLogger,
) : __DOMAIN_PASCAL__RepositoryProviders {

    @SingletonScope
    @Provides
    internal fun provide__DOMAIN_PASCAL__Repository(): __DOMAIN_PASCAL__Repository =
        __DOMAIN_PASCAL__RepositoryImpl(__DOMAIN_PASCAL__DataSource(client), logger)
}
