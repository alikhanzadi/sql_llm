```mermaid
erDiagram

    USERS ||--o{ ISSUERS : "has"
    ISSUERS ||--|| ATHLETE_PROFILE : "extends"
    ISSUERS ||--o{ IDENTITY_VERIFICATION : "verified_by"
    ISSUERS ||--o{ SOCIAL_VERIFICATION : "verified_by"
    ISSUERS ||--|| ISSUER_POST_SIGNUP : "has"
    ISSUERS ||--|| ISSUER_PREFERENCES : "configures"

    ISSUERS ||--o{ TOKENS : "mints"

    TOKENS ||--o{ TRANSACTIONS : "traded_in"

    USERS ||--o{ TRANSACTIONS : "buyer"
    USERS ||--o{ TRANSACTIONS : "seller"

    TRANSACTIONS ||--o{ ISSUER_DAILY_REVENUE : "aggregates_to"

    USERS ||--o{ USER_TOKEN_WALLET : "holds"
    TOKENS ||--o{ USER_TOKEN_WALLET : "held_as"

    USERS ||--|| USER_WALLET : "has"
```