/**
 * @author Sanghyuk Kim
 * @description Executes Identity Resolution Ruleset in Salesforce Data Cloud using Named Credential.
 *              Designed for use in Scheduled Flows with asynchronous callout.
 */
public class DataCloudIdentityResolutionService {

    // Named Credential configured in Salesforce Setup
    private static final String NAMED_CREDENTIAL = 'DataCloud_NamedCredential';

    // API version for the REST endpoint
    private static final String API_VERSION = 'v62.0';

    // DeveloperName or ID of the Identity Resolution Ruleset
    private static final String RULESET_DEVELOPER_NAME = '1irHp000000kATKIA2';

    /**
     * @description Entry point for Flow. Triggers Identity Resolution asynchronously.
     * @param dummyInput Required by Flow; not used in logic.
     */
    @InvocableMethod(
        label='Run Data Cloud IDR Ruleset',
        description='Triggers execution of Identity Resolution Ruleset via REST API.'
    )
    public static void runIdentityResolutionFromFlow(List<String> dummyInput) {
        runIdentityResolutionAsync(RULESET_DEVELOPER_NAME, 'Flow', '10');
    }

    /**
     * @description Asynchronous callout to trigger the Identity Resolution API using Named Credential.
     * @param rulesetDeveloperName The developer name or ID of the ruleset
     * @param callingApp Identifier for the caller (e.g., "Flow", "BatchJob")
     * @param callingAppInfo Optional extra context (e.g., version number, environment)
     */
    @future(callout=true)
    private static void runIdentityResolutionAsync(String rulesetDeveloperName, String callingApp, String callingAppInfo) {
        // Construct the full REST API endpoint using Named Credential
        String endpoint = 'callout:' + NAMED_CREDENTIAL + '/services/data/' + API_VERSION +
                          '/ssot/identity-resolutions/' + rulesetDeveloperName + '/actions/run-now';

        // Prepare request body
        RequestBody body = new RequestBody();
        body.callingApp = callingApp;
        body.callingAppInfo = callingAppInfo;
        String jsonBody = JSON.serialize(body);

        // Configure HTTP request
        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(jsonBody);

        // Send the request
        try {
            Http http = new Http();
            HttpResponse res = http.send(req);

            if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
                ResponsePayload response = (ResponsePayload)JSON.deserialize(res.getBody(), ResponsePayload.class);
                System.debug('Identity Resolution triggered successfully. Result Code: ' + response.resultCode);
            } else {
                System.debug(System.LoggingLevel.ERROR,
                    'Failed to trigger IDR. Status: ' + res.getStatus() +
                    ', Code: ' + res.getStatusCode() +
                    ', Body: ' + res.getBody());
            }
        } catch (Exception e) {
            System.debug(System.LoggingLevel.ERROR, 'Exception during IDR callout: ' + e.getMessage());
        }
    }

    // Inner class representing the request body
    private class RequestBody {
        public String callingApp;
        public String callingAppInfo;
    }

    // Inner class representing the response payload
    private class ResponsePayload {
        public String resultCode;
    }
}
