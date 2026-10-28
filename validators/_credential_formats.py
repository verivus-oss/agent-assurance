"""Named provider byte requirements; no expression syntax is interpreted."""

from _credential_detection import ALNUM, WORD, Capture, all_bytes, bindings, entropy, occurrences

DIGITS = b"0123456789"
LETTERS = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
HEX = b"0123456789abcdefABCDEF"
LOWER_HEX = b"0123456789abcdef"
URL_BODY = WORD + b"-"
PADDED_BODY = URL_BODY + b"="
BASE64_BODY = ALNUM + b"+/"
UUID_LENGTHS = (8, 4, 4, 4, 12)

# Context, complete body size and alphabet are protocol facts. Compound
# formats have named validators below rather than an extensible grammar.
BOUND = (
    ("adafruit-api-key", (b"adafruit",), 32, 32, URL_BODY, 0),
    ("adobe-client-id", (b"adobe",), 32, 32, HEX, 2),
    ("airtable-api-key", (b"airtable",), 17, 17, ALNUM, 0),
    ("algolia-api-key", (b"algolia",), 32, 32, ALNUM, 0),
    ("alibaba-secret-key", (b"alibaba",), 30, 30, ALNUM, 2),
    ("asana-client-id", (b"asana",), 16, 16, DIGITS, 0),
    ("asana-client-secret", (b"asana",), 32, 32, ALNUM, 0),
    ("bitbucket-client-id", (b"bitbucket",), 32, 32, ALNUM, 0),
    ("bitbucket-client-secret", (b"bitbucket",), 64, 64, PADDED_BODY, 0),
    ("bittrex-access-key", (b"bittrex",), 32, 32, ALNUM, 0),
    ("bittrex-secret-key", (b"bittrex",), 32, 32, ALNUM, 0),
    ("cisco-meraki-api-key", (b"meraki",), 40, 40, LOWER_HEX, 3),
    ("cloudflare-api-key", (b"cloudflare",), 40, 40, URL_BODY, 2),
    ("cloudflare-global-api-key", (b"cloudflare",), 37, 37, HEX, 2),
    ("codecov-access-token", (b"codecov",), 32, 32, ALNUM, 0),
    ("cohere-api-token", (b"cohere", b"co_api_key"), 40, 40, ALNUM, 4),
    ("coinbase-access-token", (b"coinbase",), 64, 64, URL_BODY, 0),
    ("confluent-access-token", (b"confluent",), 16, 16, ALNUM, 0),
    ("confluent-secret-key", (b"confluent",), 64, 64, ALNUM, 0),
    ("contentful-delivery-api-token", (b"contentful",), 43, 43, PADDED_BODY, 0),
    ("datadog-access-token", (b"datadog",), 40, 40, ALNUM, 0),
    ("discord-api-token", (b"discord",), 64, 64, HEX, 0),
    ("discord-client-id", (b"discord",), 18, 18, DIGITS, 2),
    ("discord-client-secret", (b"discord",), 32, 32, PADDED_BODY, 2),
    ("droneci-access-token", (b"droneci",), 32, 32, ALNUM, 0),
    ("dropbox-api-token", (b"dropbox",), 15, 15, ALNUM, 0),
    ("etsy-access-token", (b"etsy",), 24, 24, ALNUM, 3),
    ("facebook-secret", (b"facebook",), 32, 32, HEX, 3),
    ("fastly-api-token", (b"fastly",), 32, 32, PADDED_BODY, 0),
    ("finicity-api-token", (b"finicity",), 32, 32, HEX, 0),
    ("finicity-client-secret", (b"finicity",), 20, 20, ALNUM, 0),
    ("finnhub-access-token", (b"finnhub",), 20, 20, ALNUM, 0),
    ("flickr-access-token", (b"flickr",), 32, 32, ALNUM, 0),
    ("freshbooks-access-token", (b"freshbooks",), 64, 64, ALNUM, 0),
    ("gitter-access-token", (b"gitter",), 40, 40, URL_BODY, 0),
    ("intercom-api-key", (b"intercom",), 60, 60, PADDED_BODY, 0),
    ("jfrog-api-key", (b"jfrog", b"artifactory", b"bintray", b"xray"), 73, 73, ALNUM, 0),
    ("jfrog-identity-token", (b"jfrog", b"artifactory", b"bintray", b"xray"), 64, 64, ALNUM, 0),
    ("kraken-access-token", (b"kraken",), 80, 90, PADDED_BODY + b"+/", 0),
    ("kucoin-access-token", (b"kucoin",), 24, 24, HEX, 0),
    ("launchdarkly-access-token", (b"launchdarkly",), 40, 40, PADDED_BODY, 0),
    ("linear-client-secret", (b"linear",), 32, 32, HEX, 2),
    ("linkedin-client-id", (b"linkedin", b"linked_in", b"linked-in"), 14, 14, ALNUM, 2),
    ("linkedin-client-secret", (b"linkedin", b"linked_in", b"linked-in"), 16, 16, ALNUM, 2),
    ("looker-client-id", (b"looker",), 20, 20, ALNUM, 0),
    ("looker-client-secret", (b"looker",), 24, 24, ALNUM, 0),
    ("mattermost-access-token", (b"mattermost",), 26, 26, ALNUM, 0),
    ("messagebird-api-token", (b"messagebird", b"message_bird", b"message-bird"), 25, 25, ALNUM, 0),
    ("netlify-access-token", (b"netlify",), 40, 46, PADDED_BODY, 0),
    ("new-relic-user-api-id", (b"newrelic", b"new_relic", b"new-relic"), 64, 64, ALNUM, 0),
    ("nytimes-access-token", (b"nytimes", b"new-york-times", b"newyorktimes"), 32, 32, PADDED_BODY, 0),
    ("plaid-client-id", (b"plaid",), 24, 24, ALNUM, 3.5),
    ("plaid-secret-key", (b"plaid",), 30, 30, ALNUM, 3.5),
    ("privateai-api-token", (b"privateai", b"private_ai", b"private-ai"), 32, 32, b"abcdefghijklmnopqrstuvwxyz0123456789", 3),
    ("rapidapi-access-token", (b"rapidapi",), 50, 50, URL_BODY, 0),
    ("sendbird-access-token", (b"sendbird",), 40, 40, HEX, 0),
    ("sentry-access-token", (b"sentry",), 64, 64, HEX, 3),
    ("sumologic-access-token", (b"sumo",), 64, 64, ALNUM, 3),
    ("travisci-access-token", (b"travis",), 22, 22, ALNUM, 0),
    ("twitch-api-token", (b"twitch",), 30, 30, ALNUM, 0),
    ("twitter-access-secret", (b"twitter",), 45, 45, ALNUM, 0),
    ("twitter-api-key", (b"twitter",), 25, 25, ALNUM, 0),
    ("twitter-api-secret", (b"twitter",), 50, 50, ALNUM, 0),
    ("zendesk-secret-key", (b"zendesk",), 40, 40, ALNUM, 0),
)


def uuid_body(value):
    parts = value.split(b"-")
    return len(parts) == 5 and all(len(part) == size and all_bytes(part, HEX)
                                    for part, size in zip(parts, UUID_LENGTHS))


UUID_BOUND = (
    ("heroku-api-key", (b"heroku",)), ("hubspot-api-key", (b"hubspot",)),
    ("kucoin-secret-key", (b"kucoin",)),
    ("messagebird-client-id", (b"messagebird", b"message_bird", b"message-bird")),
    ("sendbird-access-id", (b"sendbird",)),
    ("snyk-api-token", (b"snyk_api_key", b"snyk_api_token", b"snyk_oauth_key", b"snyk_oauth_token",
                         b"snyk-key", b"snyk-token", b"snykkey", b"snyktoken")),
    ("squarespace-access-token", (b"squarespace",)),
)


def provider_bindings(data):
    for name, context_start, start, end in bindings(data):
        name = name.lower()
        value = data[start:end]
        for rule, contexts, minimum, maximum, alphabet, threshold in BOUND:
            if any(context in name for context in contexts) and minimum <= len(value) <= maximum:
                if all_bytes(value, alphabet) and entropy(value) >= threshold:
                    yield Capture(rule, data, start, end, context_start, end)
        for rule, contexts in UUID_BOUND:
            if any(context in name for context in contexts) and uuid_body(value):
                yield Capture(rule, data, start, end, context_start, end)


def boundary(data, position):
    before = position > 0 and data[position - 1] in WORD
    after = position < len(data) and data[position] in WORD
    return before != after


def terminated(data, end):
    return (end == len(data) or data[end] in b"`'\" \t\r\n\v\f;"
            or data.startswith((b"\\r", b"\\n"), end))


class Token:
    __slots__ = ("rule", "prefix", "minimum", "maximum", "alphabet", "threshold", "left", "ending", "fold")

    def __init__(self, rule, prefix, size, alphabet, threshold=0, *, left=True, ending="literal", fold=False):
        self.rule, self.prefix, self.alphabet = rule, prefix, alphabet
        self.minimum, self.maximum = size if isinstance(size, tuple) else (size, size)
        self.threshold, self.left, self.ending, self.fold = threshold, left, ending, fold
        if (not prefix or self.minimum < 0 or self.maximum is not None and self.maximum < self.minimum
                or ending not in ("literal", "word", "outside-body", "none")):
            raise ValueError("invalid fixed provider token declaration")

    def captures(self, data, folded):
        source = folded if self.fold else data
        prefix = self.prefix.lower() if self.fold else self.prefix
        resume = 0
        for start in occurrences(source, prefix):
            if start < resume:
                continue
            if self.left and not boundary(data, start):
                continue
            body = start + len(prefix)
            end = body
            stop = len(data) if self.maximum is None else min(len(data), body + self.maximum)
            while end < stop and data[end] in self.alphabet:
                end += 1
            if end - body < self.minimum:
                continue
            if self.ending == "literal" and not terminated(data, end):
                continue
            if self.ending == "word" and not boundary(data, end):
                continue
            if self.ending == "outside-body" and end < len(data) and data[end] in self.alphabet:
                continue
            resume = end
            if entropy(data[start:end]) >= self.threshold:
                yield Capture(self.rule, data, start, end)


TOKENS = (
    Token("adobe-client-secret", b"p8e-", 32, ALNUM, 2),
    Token("age-secret-key", b"AGE-SECRET-KEY-1", 58, b"QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L", left=False, ending="none"),
    Token("alibaba-access-key-id", b"LTAI", 20, ALNUM, 2),
    Token("anthropic-admin-api-key", b"sk-ant-admin01-", 95, URL_BODY),
    Token("anthropic-api-key", b"sk-ant-api03-", 95, URL_BODY),
    Token("artifactory-api-key", b"AKCp", 69, ALNUM, 4.5, ending="word"),
    Token("artifactory-reference-token", b"cmVmd", 59, ALNUM, 4.5, ending="word"),
    Token("atlassian-api-token", b"ATATT3", 186, PADDED_BODY, 3.5),
    Token("clickhouse-cloud-api-secret-key", b"4b1d", 38, ALNUM, 3, ending="word"),
    Token("clojars-api-token", b"CLOJARS_", 60, ALNUM, 2, left=False, ending="none", fold=True),
    Token("digitalocean-access-token", b"doo_v1_", 64, LOWER_HEX, 3),
    Token("digitalocean-pat", b"dop_v1_", 64, LOWER_HEX, 3),
    Token("digitalocean-refresh-token", b"dor_v1_", 64, HEX, fold=True),
    Token("doppler-api-token", b"dp.pt.", 43, ALNUM, 2, left=False, ending="none"),
    Token("duffel-api-token", b"duffel_test_", 43, PADDED_BODY, 2, left=False, ending="none"),
    Token("duffel-api-token", b"duffel_live_", 43, PADDED_BODY, 2, left=False, ending="none"),
    Token("easypost-api-token", b"EZAK", 54, ALNUM, 2, ending="word"),
    Token("easypost-test-api-token", b"EZTK", 54, ALNUM, 2, ending="word"),
    Token("facebook-page-access-token", b"EAAM", (100, None), ALNUM, 4),
    Token("facebook-page-access-token", b"EAAC", (100, None), ALNUM, 4),
    Token("frameio-api-token", b"fio-u-", 64, PADDED_BODY, left=False, ending="none"),
    Token("gcp-api-key", b"AIza", 35, URL_BODY, 4),
    Token("gitlab-deploy-token", b"gldt-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-feature-flag-client-token", b"glffct-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-feed-token", b"glft-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-incoming-mail-token", b"glimt-", 25, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-kubernetes-agent-token", b"glagent-", 50, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-oauth-app-secret", b"gloas-", 64, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-pat", b"glpat-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-ptt", b"glptt-", 40, LOWER_HEX, 3, left=False, ending="none"),
    Token("gitlab-rrt", b"GR1348941", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-runner-authentication-token", b"glrt-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-scim-token", b"glsoat-", 20, URL_BODY, 3, left=False, ending="none"),
    Token("gitlab-session-cookie", b"_gitlab_session=", 32, b"abcdefghijklmnopqrstuvwxyz0123456789", 3,
          left=False, ending="none"),
    Token("heroku-api-key-v2", b"HRKU-AA", 58, URL_BODY, 4),
    Token("huggingface-access-token", b"hf_", 34, LETTERS, 2),
    Token("huggingface-organization-api-token", b"api_org_", 34, LETTERS, 2),
    Token("infracost-api-token", b"ico-", 32, ALNUM, 3),
    Token("intra42-client-secret", b"s-s4t2ud-", 64, HEX, 3),
    Token("intra42-client-secret", b"s-s4t2af-", 64, HEX, 3),
    Token("linear-api-key", b"lin_api_", 40, ALNUM, 2, left=False, ending="none"),
    Token("npm-access-token", b"npm_", 36, ALNUM, 2, fold=True),
    Token("octopus-deploy-api-key", b"API-", 26, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 3),
    Token("openshift-user-token", b"sha256~", 43, URL_BODY, 3.5, ending="outside-body"),
    Token("perplexity-api-key", b"pplx-", 48, ALNUM, 4, ending="word"),
    Token("planetscale-api-token", b"pscale_tkn_", (32, 64), WORD + b"=.-", 3),
    Token("planetscale-oauth-token", b"pscale_oauth_", (32, 64), WORD + b"=.-", 3),
    Token("planetscale-password", b"pscale_pw_", (32, 64), WORD + b"=.-", 3, fold=True),
    Token("prefect-api-token", b"pnu_", 36, ALNUM, 2),
    Token("pulumi-api-token", b"pul-", 40, LOWER_HEX, 2),
    Token("pypi-upload-token", b"pypi-AgEIcHlwaS5vcmc", (50, 1000), URL_BODY, 3, left=False, ending="none"),
    Token("readme-api-token", b"rdme_", 70, b"abcdefghijklmnopqrstuvwxyz0123456789", 2),
    Token("rubygems-api-token", b"rubygems_", 48, LOWER_HEX, 2),
    Token("scalingo-api-token", b"tk-us-", 48, URL_BODY, 2),
    Token("sendgrid-api-token", b"SG.", 66, PADDED_BODY + b".", 2),
    Token("sentry-user-token", b"sntryu_", 64, LOWER_HEX, 3.5),
    Token("settlemint-application-access-token", b"sm_aat_", 16, ALNUM, 3),
    Token("settlemint-personal-access-token", b"sm_pat_", 16, ALNUM, 3),
    Token("settlemint-service-access-token", b"sm_sat_", 16, ALNUM, 3),
    Token("shippo-api-token", b"shippo_live_", 40, HEX, 2),
    Token("shippo-api-token", b"shippo_test_", 40, HEX, 2),
    Token("shopify-access-token", b"shpat_", 32, HEX, 2, left=False, ending="none"),
    Token("shopify-custom-access-token", b"shpca_", 32, HEX, 2, left=False, ending="none"),
    Token("shopify-private-app-access-token", b"shppa_", 32, HEX, 2, left=False, ending="none"),
    Token("shopify-shared-secret", b"shpss_", 32, HEX, 2, left=False, ending="none"),
    Token("square-access-token", b"EAAA", (22, 60), URL_BODY, 2),
    Token("square-access-token", b"sq0atp-", (22, 60), URL_BODY, 2),
    Token("stripe-access-token", b"sk_test_", (10, 99), ALNUM, 2),
    Token("stripe-access-token", b"sk_live_", (10, 99), ALNUM, 2),
    Token("stripe-access-token", b"sk_prod_", (10, 99), ALNUM, 2),
    Token("stripe-access-token", b"rk_test_", (10, 99), ALNUM, 2),
    Token("stripe-access-token", b"rk_live_", (10, 99), ALNUM, 2),
    Token("stripe-access-token", b"rk_prod_", (10, 99), ALNUM, 2),
    Token("twilio-api-key", b"SK", 32, HEX, 3, left=False, ending="none"),
    Token("vault-batch-token", b"hvb.", (138, 300), URL_BODY, 4),
    Token("vault-service-token", b"hvs.", (90, 120), URL_BODY, 3.5),
    Token("vault-service-token", b"s.", 24, ALNUM, 3.5),
)


def provider_tokens(data):
    folded = data.lower()
    for token in TOKENS:
        for capture in token.captures(data, folded):
            if token.rule in ("anthropic-api-key", "anthropic-admin-api-key"):
                if data[capture.end - 2:capture.end] != b"AA":
                    continue
            yield capture
