package __BASE_PACKAGE__.domain.__DOMAIN__.entities

sealed class __DOMAIN_PASCAL__EntityResult {
    data class Success(val items: List<__DOMAIN_PASCAL__Entity>) : __DOMAIN_PASCAL__EntityResult()
    data class Failure(val reason: __DOMAIN_PASCAL__FailureReason) : __DOMAIN_PASCAL__EntityResult()
}
