@resource_type_validation
Feature: Resource type validation

    Scenario: As an evil user, when I try to upload a resource with a MIME type not matching its extension, I should get an error
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset with key-value parameters "notes=Testing resource type mismatch"
        And I open the new resource form for dataset "$last_generated_name"
        And I create a resource with key-value parameters "name=Testing EICAR PDF::description=Testing EICAR sample virus file with PDF extension::format=PDF::upload=eicar.com.pdf"
        Then I should see "Mismatched file type"

    Scenario: As a publisher, when I create a resource linking to an internal URL, I should not see any type mismatch errors
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "notes=Testing internal URL" and "name=Internal link::url=http://ckan:5000/api/action/status_show"
        Then I should see "Testing internal URL"
