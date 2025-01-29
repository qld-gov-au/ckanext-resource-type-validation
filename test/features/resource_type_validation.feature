Feature: Resource type validation

    Scenario: As an evil user, when I try to upload a resource with a MIME type not matching its extension, I should get an error
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset with key-value parameters "notes=Testing mismatched MIME type"
        And I open the new resource form for dataset "$last_generated_name"
        And I fill in default resource fields
        And I upload "eicar.com.pdf" of type "PDF" to resource
        And I press the element with xpath "//form[contains(@class, 'resource-form')]//button[contains(@class, 'btn-primary')]"
        Then I should see "Mismatched file type"
