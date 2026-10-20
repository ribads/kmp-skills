package __BASE_PACKAGE__.domain.session.entities.di

import __BASE_PACKAGE__.domain.session.entities.SessionRepository

interface SessionRepositoryProviders {
    val sessionRepository: SessionRepository
}
