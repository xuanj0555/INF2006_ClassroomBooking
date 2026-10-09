# Cognito configuration

Recorded on: 10 October 2026

## User pool

Region: us-east-1  
User pool ID: us-east-1_EtQjacsSX  
Issuer: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EtQjacsSX

## App client

Name: roomly-web  
Client ID: 7bqthe08cf0fovnaqa43chjec5  
Client secret: None

## Token and authentication settings

- Authentication flow session duration: 3 minutes
- Access token expiration: 60 minutes
- ID token expiration: 60 minutes
- Refresh token expiration: 5 days
- Token revocation: Enabled
- Prevent user existence errors: Enabled

The displayed authentication flows are:
- Choice-based sign-in
- Secure remote password (SRP)
- Get user tokens from existing authenticated sessions

## Managed login configuration

Status: Available  
Identity provider: Cognito user pool directory

Allowed callback URL: http://127.0.0.1:8766/  
Allowed sign-out URL: http://127.0.0.1:8766/  
Default redirect URI: Not configured

OAuth grant type: Authorization code grant

OpenID Connect scopes:
- email
- openid

Custom scopes: None

Users authenticate through Cognito's managed login page. After authentication, Cognito redirects the browser to the configured callback URL. After sign-out, users return to the configured sign-out URL.
