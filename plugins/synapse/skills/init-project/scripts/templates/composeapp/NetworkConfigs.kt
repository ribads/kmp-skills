package __APP_PACKAGE__.di

import __APP_PACKAGE__.AppEnvironment
import co.touchlab.kermit.Logger
import com.ribads.synapse.core.network.HttpLogger
import com.ribads.synapse.core.network.HttpLogging
import com.ribads.synapse.core.network.NetworkConfig

internal fun AppEnvironment.toNetworkConfig(): NetworkConfig = NetworkConfig(
    baseUrl = apiBaseUrl,
    logging = if (verboseNetworkLogging) HttpLogging.Body(KermitHttpLogger) else HttpLogging.None,
)

private object KermitHttpLogger : HttpLogger {
    private val kermit = Logger.withTag("Http")

    override fun log(message: String) {
        kermit.d(message)
    }
}
