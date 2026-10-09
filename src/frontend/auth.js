// Public SPA configuration. Passwords are entered only on Cognito's login page.
window.roomlyAuth = (() => {
  const domain = 'https://us-east-1etqjacssx.auth.us-east-1.amazoncognito.com';
  const clientId = '7bqthe08cf0fovnaqa43chjec5';
  const issuer = 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EtQjacsSX';
  const redirect = location.origin + '/';
  const flowKey = 'roomly.cognito.flow';
  const tokenKey = 'roomly.cognito.access';
  const encode = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const random = () => encode(crypto.getRandomValues(new Uint8Array(32)));
  function read(key) {
    try { return JSON.parse(sessionStorage.getItem(key) || 'null'); }
    catch { sessionStorage.removeItem(key); return null; }
  }
  function token() {
    const saved = read(tokenKey);
    if (!saved || saved.expires <= Date.now() + 30000) {
      sessionStorage.removeItem(tokenKey);
      return null;
    }
    return saved.access;
  }
  async function signIn() {
    const verifier = random(), state = random(), nonce = random();
    const challenge = encode(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))));
    sessionStorage.removeItem(tokenKey);
    sessionStorage.setItem(flowKey, JSON.stringify({verifier, state, nonce, created: Date.now(), redirect}));
    const params = new URLSearchParams({client_id: clientId, redirect_uri: redirect,
      response_type: 'code', scope: 'openid email', state, nonce,
      code_challenge_method: 'S256', code_challenge: challenge});
    location.assign(domain + '/oauth2/authorize?' + params);
  }
  async function callback() {
    const params = new URLSearchParams(location.search);
    if (!params.has('code') && !params.has('error')) return;
    const flow = read(flowKey);
    sessionStorage.removeItem(flowKey);
    sessionStorage.removeItem(tokenKey);
    history.replaceState({}, '', location.pathname);
    if (!flow || params.get('state') !== flow.state || Date.now() - flow.created > 600000 || flow.redirect !== redirect) {
      throw Error('Sign-in could not be verified. Click Sign in and try again.');
    }
    if (params.has('error')) throw Error('Sign-in was not completed. Please try again.');
    const response = await fetch(domain + '/oauth2/token', {
      method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({grant_type: 'authorization_code', client_id: clientId,
        code: params.get('code'), redirect_uri: redirect, code_verifier: flow.verifier})
    });
    const result = await response.json();
    if (!response.ok || !result.access_token || !result.id_token || result.token_type?.toLowerCase() !== 'bearer') {
      throw Error('Cognito could not complete sign-in. Please try again.');
    }
    // Inspect correlation fields only; API Gateway verifies the access-token signature.
    let claims;
    try {
      const part = result.id_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      claims = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(part), c => c.charCodeAt(0))));
    } catch { throw Error('Unexpected sign-in response. Please try again.'); }
    if (claims.nonce !== flow.nonce || claims.iss !== issuer || claims.aud !== clientId || claims.exp * 1000 <= Date.now()) {
      throw Error('Unexpected sign-in response. Please try again.');
    }
    const seconds = Number(result.expires_in);
    if (!Number.isFinite(seconds) || seconds <= 0) throw Error('Invalid sign-in expiry.');
    // Discard ID and refresh tokens; require sign-in again when the access token expires.
    sessionStorage.setItem(tokenKey, JSON.stringify({access: result.access_token, expires: Date.now() + seconds * 1000}));
  }
  function signOut() {
    sessionStorage.removeItem(tokenKey);
    sessionStorage.removeItem(flowKey);
    location.assign(domain + '/logout?' + new URLSearchParams({client_id: clientId, logout_uri: redirect}));
  }
  return {token, signIn, signOut, callback};
})();
