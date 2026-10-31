"""Public, unissued examples for the pinned credential coverage population.

The examples are independent of the detector declarations. They are also
measured against the old pinned detector before its retirement; agreement
with that implementation is separate from the declared byte expectations.
"""

import binascii
import hashlib

LETTERS = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALNUM = LETTERS + b"0123456789"
HEX = b"0123456789abcdef"
URL = ALNUM + b"_-"
B64 = ALNUM + b"+/"
DIGITS = b"0123456789"


def opaque(length, alphabet=ALNUM, salt=None):
    result = bytearray()
    counter = 0
    while len(result) < length:
        prefix = b"public credential control " if salt is None else b"public credential control " + salt + b" "
        block = hashlib.sha256(prefix + str(counter).encode()).digest()
        result.extend(alphabet[byte % len(alphabet)] for byte in block)
        counter += 1
    return bytes(result[:length])


def corpus():
    cases, rejected = [], []
    def add(rule, value, context=None, path=None, variant="canonical", body_offset=None):
        source = value if context is None else context + b'="' + value + b'"'
        cases.append({"id": rule + "/" + variant, "rule": rule, "source": source, "path": path})
        if body_offset is not None:
            invalid = value[:body_offset] + b"\xff" + value[body_offset + 1:]
            source = invalid if context is None else context + b'="' + invalid + b'"'
            rejected.append({"id": rule + "/invalid-body-byte", "rule": rule, "source": source, "path": path})

    # Contextual values from the reference rule contracts. These inputs do
    # not read body sizes or alphabets from the implementation under test.
    ordinary = (
        ("adafruit-api-key", b"adafruit", 32, URL), ("adobe-client-id", b"adobe", 32, HEX),
        ("airtable-api-key", b"airtable", 17, ALNUM), ("algolia-api-key", b"algolia", 32, ALNUM),
        ("alibaba-secret-key", b"alibaba", 30, ALNUM), ("asana-client-id", b"asana", 16, DIGITS),
        ("asana-client-secret", b"asana", 32, ALNUM), ("bitbucket-client-id", b"bitbucket", 32, ALNUM),
        ("bitbucket-client-secret", b"bitbucket", 64, URL), ("bittrex-access-key", b"bittrex", 32, ALNUM),
        ("bittrex-secret-key", b"bittrex", 32, ALNUM), ("cisco-meraki-api-key", b"meraki", 40, HEX),
        ("cloudflare-api-key", b"cloudflare", 40, URL), ("cloudflare-global-api-key", b"cloudflare", 37, HEX),
        ("codecov-access-token", b"codecov", 32, ALNUM), ("cohere-api-token", b"cohere", 40, ALNUM),
        ("coinbase-access-token", b"coinbase", 64, URL), ("confluent-access-token", b"confluent", 16, ALNUM),
        ("confluent-secret-key", b"confluent", 64, ALNUM), ("contentful-delivery-api-token", b"contentful", 43, URL),
        ("datadog-access-token", b"datadog", 40, ALNUM), ("discord-api-token", b"discord", 64, HEX),
        ("discord-client-id", b"discord", 18, DIGITS), ("discord-client-secret", b"discord", 32, URL),
        ("droneci-access-token", b"droneci", 32, ALNUM), ("dropbox-api-token", b"dropbox", 15, ALNUM),
        ("etsy-access-token", b"etsy", 24, ALNUM), ("facebook-secret", b"facebook", 32, HEX),
        ("fastly-api-token", b"fastly", 32, URL), ("finicity-api-token", b"finicity", 32, HEX),
        ("finicity-client-secret", b"finicity", 20, ALNUM), ("finnhub-access-token", b"finnhub", 20, ALNUM),
        ("flickr-access-token", b"flickr", 32, ALNUM), ("freshbooks-access-token", b"freshbooks", 64, ALNUM),
        ("gitter-access-token", b"gitter", 40, URL), ("intercom-api-key", b"intercom", 60, URL),
        ("jfrog-api-key", b"jfrog", 73, ALNUM), ("jfrog-identity-token", b"jfrog", 64, ALNUM),
        ("kraken-access-token", b"kraken", 84, B64), ("kucoin-access-token", b"kucoin", 24, HEX),
        ("launchdarkly-access-token", b"launchdarkly", 40, URL), ("linear-client-secret", b"linear", 32, HEX),
        ("linkedin-client-id", b"linkedin", 14, ALNUM), ("linkedin-client-secret", b"linkedin", 16, ALNUM),
        ("looker-client-id", b"looker", 20, ALNUM), ("looker-client-secret", b"looker", 24, ALNUM),
        ("mattermost-access-token", b"mattermost", 26, ALNUM), ("messagebird-api-token", b"messagebird", 25, ALNUM),
        ("netlify-access-token", b"netlify", 43, URL), ("new-relic-user-api-id", b"newrelic", 64, ALNUM),
        ("nytimes-access-token", b"nytimes", 32, URL), ("plaid-client-id", b"plaid", 24, ALNUM),
        ("plaid-secret-key", b"plaid", 30, ALNUM), ("privateai-api-token", b"privateai", 32, b"abcdefghijklmnopqrstuvwxyz0123456789"),
        ("rapidapi-access-token", b"rapidapi", 50, URL), ("sendbird-access-token", b"sendbird", 40, HEX),
        ("sentry-access-token", b"sentry", 64, HEX), ("sumologic-access-token", b"sumo", 64, ALNUM),
        ("travisci-access-token", b"travis", 22, ALNUM), ("twitch-api-token", b"twitch", 30, ALNUM),
        ("twitter-access-secret", b"twitter", 45, ALNUM), ("twitter-api-key", b"twitter", 25, ALNUM),
        ("twitter-api-secret", b"twitter", 50, ALNUM), ("zendesk-secret-key", b"zendesk", 40, ALNUM),
    )
    for rule, context, length, alphabet in ordinary:
        add(rule, opaque(length, alphabet), context + b"_token", body_offset=0)
    identifier = b"2d82f493-51a6-4e87-9b01-5d3e8f41b20c"
    for rule, context in (("heroku-api-key", b"heroku"), ("hubspot-api-key", b"hubspot"),
                          ("kucoin-secret-key", b"kucoin"), ("messagebird-client-id", b"messagebird"),
                          ("sendbird-access-id", b"sendbird"), ("snyk-api-token", b"snyk_api_key"),
                          ("squarespace-access-token", b"squarespace")):
        add(rule, identifier, context, body_offset=0)
    fixed = (
        ("github-pat", b"ghp_", 36, ALNUM), ("github-oauth", b"gho_", 36, ALNUM),
        ("github-app-token", b"ghu_", 36, ALNUM), ("github-refresh-token", b"ghr_", 36, ALNUM),
        ("github-fine-grained-pat", b"github_pat_", 82, ALNUM),
        ("adobe-client-secret", b"p8e-", 32, ALNUM),
        ("age-secret-key", b"AGE-SECRET-KEY-1", 58, b"QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L"),
        ("alibaba-access-key-id", b"LTAI", 20, ALNUM), ("artifactory-api-key", b"AKCp", 69, ALNUM),
        ("artifactory-reference-token", b"cmVmd", 59, ALNUM), ("atlassian-api-token", b"ATATT3", 186, URL),
        ("clickhouse-cloud-api-secret-key", b"4b1d", 38, ALNUM), ("clojars-api-token", b"CLOJARS_", 60, ALNUM),
        ("digitalocean-access-token", b"doo_v1_", 64, HEX), ("digitalocean-pat", b"dop_v1_", 64, HEX),
        ("digitalocean-refresh-token", b"dor_v1_", 64, HEX), ("doppler-api-token", b"dp.pt.", 43, ALNUM),
        ("duffel-api-token", b"duffel_live_", 43, URL), ("easypost-api-token", b"EZAK", 54, ALNUM),
        ("easypost-test-api-token", b"EZTK", 54, ALNUM), ("facebook-page-access-token", b"EAAM", 120, ALNUM),
        ("frameio-api-token", b"fio-u-", 64, URL), ("gcp-api-key", b"AIza", 35, URL),
        ("gitlab-deploy-token", b"gldt-", 20, URL), ("gitlab-feature-flag-client-token", b"glffct-", 20, URL),
        ("gitlab-feed-token", b"glft-", 20, URL), ("gitlab-incoming-mail-token", b"glimt-", 25, URL),
        ("gitlab-kubernetes-agent-token", b"glagent-", 50, URL), ("gitlab-oauth-app-secret", b"gloas-", 64, URL),
        ("gitlab-pat", b"glpat-", 20, URL), ("gitlab-ptt", b"glptt-", 40, HEX),
        ("gitlab-rrt", b"GR1348941", 20, URL), ("gitlab-runner-authentication-token", b"glrt-", 20, URL),
        ("gitlab-scim-token", b"glsoat-", 20, URL), ("gitlab-session-cookie", b"_gitlab_session=", 32, b"abcdefghijklmnopqrstuvwxyz0123456789"),
        ("heroku-api-key-v2", b"HRKU-AA", 58, URL), ("huggingface-access-token", b"hf_", 34, LETTERS),
        ("huggingface-organization-api-token", b"api_org_", 34, LETTERS), ("infracost-api-token", b"ico-", 32, ALNUM),
        ("intra42-client-secret", b"s-s4t2ud-", 64, HEX), ("linear-api-key", b"lin_api_", 40, ALNUM),
        ("npm-access-token", b"npm_", 36, ALNUM), ("octopus-deploy-api-key", b"API-", 26, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        ("openshift-user-token", b"sha256~", 43, URL), ("perplexity-api-key", b"pplx-", 48, ALNUM),
        ("planetscale-api-token", b"pscale_tkn_", 48, URL), ("planetscale-oauth-token", b"pscale_oauth_", 48, URL),
        ("planetscale-password", b"pscale_pw_", 48, URL), ("prefect-api-token", b"pnu_", 36, ALNUM),
        ("pulumi-api-token", b"pul-", 40, HEX), ("pypi-upload-token", b"pypi-AgEIcHlwaS5vcmc", 60, URL),
        ("readme-api-token", b"rdme_", 70, b"abcdefghijklmnopqrstuvwxyz0123456789"), ("rubygems-api-token", b"rubygems_", 48, HEX),
        ("scalingo-api-token", b"tk-us-", 48, URL), ("sendgrid-api-token", b"SG.", 66, URL),
        ("sentry-user-token", b"sntryu_", 64, HEX), ("settlemint-application-access-token", b"sm_aat_", 16, ALNUM),
        ("settlemint-personal-access-token", b"sm_pat_", 16, ALNUM), ("settlemint-service-access-token", b"sm_sat_", 16, ALNUM),
        ("shippo-api-token", b"shippo_live_", 40, HEX), ("shopify-access-token", b"shpat_", 32, HEX),
        ("shopify-custom-access-token", b"shpca_", 32, HEX), ("shopify-private-app-access-token", b"shppa_", 32, HEX),
        ("shopify-shared-secret", b"shpss_", 32, HEX), ("square-access-token", b"sq0atp-", 40, URL),
        ("stripe-access-token", b"sk_live_", 40, ALNUM), ("twilio-api-key", b"SK", 32, HEX),
        ("vault-batch-token", b"hvb.", 150, URL), ("vault-service-token", b"hvs.", 100, URL),
    )
    for rule, prefix, length, alphabet in fixed:
        add(rule, prefix + opaque(length, alphabet), body_offset=len(prefix))
    add("generic-api-key", b"0123456789abcdef", b"token")
    for rule, prefix in (("anthropic-api-key", b"sk-ant-api03-"), ("anthropic-admin-api-key", b"sk-ant-admin01-")):
        add(rule, prefix + opaque(93, URL) + b"AA")
    add("1password-secret-key", b"A3-" + opaque(6, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + b"-"
        + opaque(11, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", b"middle") + b"-"
        + b"-".join(opaque(5, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", str(index).encode()) for index in range(3)))
    add("1password-service-account-token", b"ops_eyJ" + opaque(260, B64))
    add("airtable-personnal-access-token", b"pat" + opaque(14) + b"." + opaque(64, HEX), b"airtable_token")
    add("aws-access-token", b"AKIA" + opaque(16, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"))
    add("aws-amazon-bedrock-api-key-long-lived", b"ABSK" + opaque(120, B64))
    add("aws-amazon-bedrock-api-key-short-lived", b"bedrock-api-key-" + b"YmVkcm9jay5hbWF6b25hd3MuY29t")
    add("azure-ad-client-secret", b"Ab3" + b"8Q~" + opaque(32, URL))
    add("authress-service-client-access-key", b"sc_" + opaque(10) + b"." + opaque(5) + b".acc-" + opaque(15) + b"." + opaque(40, B64))
    add("cloudflare-origin-ca-key", b"v1.0-" + opaque(24, HEX) + b"-" + opaque(146, HEX))
    add("databricks-api-token", b"dapi" + opaque(32, HEX) + b"-2")
    add("dynatrace-api-token", b"dt0c01." + opaque(24) + b"." + opaque(64))
    for rule, prefix in (("flutterwave-public-key", b"FLWPUBK_TEST-"), ("flutterwave-secret-key", b"FLWSECK_TEST-")):
        add(rule, prefix + opaque(32, b"abcdefgh0123456789") + b"-X")
    add("flutterwave-encryption-key", b"FLWSECK_TEST-" + opaque(12, b"abcdefgh0123456789"))
    add("flyio-access-token", b"fo1_" + opaque(43, URL))
    add("grafana-api-key", b"eyJrIjoi" + opaque(90))
    add("grafana-cloud-api-token", b"glc_" + opaque(60, B64))
    add("grafana-service-account-token", b"glsa_" + opaque(32) + b"_" + opaque(8, HEX))
    add("harness-api-key", b"pat." + opaque(22, URL) + b"." + opaque(24) + b"." + opaque(20))
    add("hashicorp-tf-api-token", opaque(14) + b".atlasv1." + opaque(65, URL))
    add("notion-api-token", b"ntn_" + opaque(11, DIGITS) + opaque(35))
    add("openai-api-key", b"sk-proj-" + opaque(58, URL) + b"T3BlbkFJ" + opaque(74, URL))
    add("postman-api-token", b"PMAK-" + opaque(24, HEX) + b"-" + opaque(34, HEX))
    add("sendinblue-api-token", b"xkeysib-" + opaque(64, HEX) + b"-" + opaque(16))
    add("beamer-api-token", b"b_" + opaque(44, URL), b"beamer_token")
    add("dropbox-long-lived-api-token", opaque(11) + b"AAAAAAAAAA" + opaque(43, URL), b"dropbox_token")
    add("dropbox-short-lived-api-token", b"sl." + opaque(135, URL), b"dropbox_token")
    add("defined-networking-api-token", b"dnkey-" + opaque(26, URL) + b"-" + opaque(52, URL), b"dnkey")
    add("gocardless-api-token", b"live_" + opaque(40, URL), b"gocardless_token")
    add("lob-api-key", b"live_" + opaque(35, HEX), b"lob_token")
    add("lob-pub-api-key", b"test_pub_" + opaque(31, HEX), b"lob_token")
    add("mailchimp-api-key", opaque(32, HEX) + b"-us12", b"mailchimp_token")
    add("mailgun-private-api-token", b"key-" + opaque(32, HEX), b"mailgun_token")
    add("mailgun-pub-key", b"pubkey-" + opaque(32, HEX), b"mailgun_token")
    add("mailgun-signing-key", opaque(32, b"abcdefgh0123456789") + b"-" + opaque(8, HEX) + b"-" + opaque(8, HEX), b"mailgun_token")
    add("mapbox-api-token", b"pk." + opaque(60) + b"." + opaque(22), b"mapbox_token")
    add("plaid-api-token", b"access-sandbox-" + identifier, b"plaid_token")
    add("sidekiq-secret", opaque(8, HEX) + b":" + opaque(8, HEX), b"BUNDLE_GEMS__CONTRIBSYS__COM")
    add("sidekiq-sensitive-url", b"https://" + opaque(8, HEX) + b":" + opaque(8, HEX) + b"@gems.contribsys.com/")
    add("sumologic-access-id", b"su" + opaque(12), b"sumo_token")
    add("telegram-bot-api-token", opaque(10, DIGITS) + b":A" + opaque(34, URL), b"telegram_token")
    add("twitter-access-token", opaque(20, DIGITS) + b"-" + opaque(30), b"twitter_token")
    add("twitter-bearer-token", b"A" * 22 + opaque(90), b"twitter_token")
    add("yandex-access-token", b"t1." + opaque(40, URL) + b"." + opaque(86, URL), b"yandex_token")
    add("yandex-api-key", b"AQVN" + opaque(36, URL), b"yandex_token")
    add("yandex-aws-access-token", b"YC" + opaque(38, URL), b"yandex_token")
    add("typeform-api-token", b"tfp_" + opaque(59, URL), b"typeform_token")
    add("okta-access-token", b"00" + opaque(40, URL), b"okta_token")
    add("sonar-api-token", b"squ_" + opaque(40, URL), b"sonar_token")
    for rule, prefix in (("new-relic-browser-api-token", b"NRJS-"), ("new-relic-insert-key", b"NRII-"), ("new-relic-user-api-key", b"NRAK-")):
        size = 19 if prefix == b"NRJS-" else 32 if prefix == b"NRII-" else 27
        add(rule, prefix + opaque(size, HEX if size == 19 else ALNUM), b"newrelic_token")
    add("gitlab-cicd-job-token", b"glcbt-" + opaque(3) + b"_" + opaque(20, URL))
    add("gitlab-pat-routable", b"glpat-" + opaque(50, URL) + b"." + opaque(9, b"abcdefghijklmnopqrstuvwxyz0123456789"))
    add("gitlab-runner-authentication-token-routable", b"glrt-t4_" + opaque(50, URL) + b"." + opaque(9, b"abcdefghijklmnopqrstuvwxyz0123456789"))
    add("maxmind-license-key", opaque(6) + b"_" + opaque(29) + b"_mmk")
    add("sourcegraph-access-token", b"sgp_" + opaque(40, HEX))
    add("facebook-access-token", opaque(15, DIGITS) + b"|" + opaque(35, URL), b"facebook_token")
    add("sentry-org-token", b"sntrys_eyJpYXQiO" + opaque(30, B64) + b"LCJyZWdpb25fdXJs" + opaque(30, B64) + b"_" + opaque(43, B64))
    token = (b"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" + b"."
             + b"eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0" + b"." + opaque(43, URL))
    add("jwt", token)
    add("jwt-base64", binascii.b2a_base64(token, newline=False))
    add("private-key", b"-----BE" + b"GIN PRIVATE KEY-----\n" + opaque(96, B64) + b"\n-----EN" + b"D PRIVATE KEY-----")
    add("slack-app-token", b"xapp-1-" + opaque(15) + b"-" + opaque(12, DIGITS) + b"-" + opaque(40))
    add("slack-bot-token", b"xoxb-" + opaque(12, DIGITS) + b"-" + opaque(12, DIGITS) + b"-" + opaque(24))
    add("slack-legacy-bot-token", b"xoxb-" + opaque(10, DIGITS) + b"-" + opaque(22))
    add("slack-user-token", b"xoxp-" + b"-".join(opaque(12, DIGITS) for _ in range(3)) + b"-" + opaque(30))
    add("slack-legacy-token", b"xoxo-" + b"-".join(opaque(10, DIGITS) for _ in range(3)) + b"-" + opaque(30, HEX))
    add("slack-legacy-workspace-token", b"xoxa-1-" + opaque(30))
    add("slack-config-access-token", b"xoxe.xoxb-1-" + opaque(165))
    add("slack-config-access-token", b"keyword xoxe.xoxb-\nxoxe/xoxp-1-" + opaque(165), variant="alternate-separator")
    add("slack-config-access-token", b"keyword xoxe.xoxp-\nxoxe" + "\u2603".encode() + b"xoxb-1-" + opaque(165), variant="unicode-separator")
    add("slack-config-refresh-token", b"xoxe-1-" + opaque(146))
    add("slack-webhook-url", b"https://hooks.slack.com/services/" + opaque(50, B64))
    add("microsoft-teams-webhook", b"https://team.webhook.office.com/webhookb2/" + identifier + b"@" + identifier + b"/IncomingWebhook/" + opaque(32, b"abcdefghijklmnopqrstuvwxyz0123456789") + b"/" + identifier)
    add("curl-auth-user", b"curl " + b"--" + b"user 'operator:" + opaque(24) + b"' https://example.invalid")
    add("curl-auth-header", b"curl -H 'Authorization: Bearer " + opaque(40) + b"' https://example.invalid")
    add("pkcs12-file", b"public binary-container filename control", path="fixture.p12")
    add("freemius-secret-key", b"<?php $settings = ['secret_key' => 'sk_" + opaque(29) + b"'];", path="fixture.php")
    add("hashicorp-tf-password", b'password = "' + opaque(12, URL) + b'"', path="fixture.tf")
    add("nuget-config-password", b'<add key="Password" value="' + opaque(20) + b'" />', path="NuGet.Config")
    add("kubernetes-secret-yaml", b"kind: Secret\ndata:\n  credential: " + binascii.b2a_base64(b"public fixture password", newline=False) + b"\n", path="fixture.yaml")
    return cases, rejected


def controls():
    return corpus()[0]


def rejections():
    return corpus()[1]
