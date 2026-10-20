package __APP_PACKAGE__.di

import __BASE_PACKAGE__.core.log.ErrorLogger
import co.touchlab.kermit.Logger

internal fun buildErrorLogger(): ErrorLogger = KermitErrorLogger(Logger.withTag("__PROJECT_NAME__"))

private class KermitErrorLogger(private val logger: Logger) : ErrorLogger {

    override fun log(message: String) {
        logger.e(message)
    }

    override fun log(throwable: Throwable) {
        logger.e(throwable.message ?: throwable::class.simpleName.orEmpty(), throwable)
    }
}
