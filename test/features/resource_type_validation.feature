Feature: Resource type validation

    Scenario: As an evil user, when I try to upload a resource with a MIME type not matching its extension, I should get an error
        Given "TestOrgEditor" as the persona
        When I log in
        And I go to dataset "warandpeace"
        And I press "Manage"
        And I press "Resources"
        And I press "Add new resource"
        And I attach the file "eicar.com.pdf" to "upload"
        And I fill in "name" with "Testing EICAR PDF"
        And I fill in "description" with "Testing EICAR sample virus file with PDF extension"
        And I execute the script "document.getElementById('field-format').value='PDF'"
        And I press the element with xpath "//form[contains(@class, 'resource-form')]//button[contains(@class, 'btn-primary')]"
        Then I should see "Mismatched file type"
