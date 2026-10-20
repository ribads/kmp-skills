package __BASE_PACKAGE__.domain.__DOMAIN__.data

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.__DOMAIN_PASCAL__DataSource
import __BASE_PACKAGE__.domain.__DOMAIN__.data.datasource.dto.__DOMAIN_PASCAL__Dto
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Entity
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__EntityResult
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__FailureReason
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository
import com.ribads.synapse.core.network.NetworkFailure
import com.ribads.synapse.core.network.toNetworkFailure
import kotlin.coroutines.cancellation.CancellationException

internal class __DOMAIN_PASCAL__RepositoryImpl(
    private val dataSource: __DOMAIN_PASCAL__DataSource,
    private val logger: ErrorLogger,
) : __DOMAIN_PASCAL__Repository {

    override suspend fun fetch(): __DOMAIN_PASCAL__EntityResult = runCatching {
        __DOMAIN_PASCAL__EntityResult.Success(dataSource.fetch().map { it.toEntity() })
    }.getOrElse {
        if (it is CancellationException) throw it
        logger.log(it)
        __DOMAIN_PASCAL__EntityResult.Failure(it.toNetworkFailure().toFailureReason())
    }

    private fun __DOMAIN_PASCAL__Dto.toEntity() = __DOMAIN_PASCAL__Entity(id = id, name = name)

    private fun NetworkFailure.toFailureReason(): __DOMAIN_PASCAL__FailureReason = when (this) {
        NetworkFailure.Offline, NetworkFailure.Timeout -> __DOMAIN_PASCAL__FailureReason.Connectivity
        NetworkFailure.Unauthorized -> __DOMAIN_PASCAL__FailureReason.Unauthorized
        is NetworkFailure.Http, NetworkFailure.Malformed, NetworkFailure.Unexpected -> __DOMAIN_PASCAL__FailureReason.Unexpected
    }
}
