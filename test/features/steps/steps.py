import email
import quopri
import six
import uuid

from behave import when, then
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.mail.steps import *  # noqa: F401, F403
from behaving.web.steps import *  # noqa: F401, F403

# Monkey-patch Selenium 3 to handle Python 3.9
import base64
if not hasattr(base64, 'encodestring'):
    base64.encodestring = base64.encodebytes


@when(u'I take a debugging screenshot')
def debug_screenshot(context):
    """ Take a screenshot only if debugging is enabled in the persona.
    """
    if context.persona and context.persona.get('debug') == 'True':
        context.execute_steps(u"""
            When I take a screenshot
        """)


@when(u'I go to homepage')
def go_to_home(context):
    context.execute_steps(u"""
        When I visit "/"
    """)


@when(u'I go to register page')
def go_to_register_page(context):
    context.execute_steps(u"""
        When I go to homepage
        And I press "Register"
    """)


@when(u'I log in')
def log_in(context):
    context.execute_steps(u"""
        When I go to homepage
        And I expand the browser height
        And I press "Log in"
        And I log in directly
    """)


@when(u'I expand the browser height')
def expand_height(context):
    # Work around x=null bug in Selenium set_window_size
    context.browser.driver.set_window_rect(x=0, y=0, width=1024, height=3072)


@when(u'I log in directly')
def log_in_directly(context):
    """
    This differs to the `log_in` function above by logging in directly to a page where the user login form is presented
    :param context:
    :return:
    """

    assert context.persona, "A persona is required to log in, found [{}] in context. Have you configured the personas in before_scenario?".format(context.persona)
    context.execute_steps(u"""
        When I attempt to log in with password "$password"
        Then I should see an element with xpath "//*[@title='Log out']/i[contains(@class, 'fa-sign-out')]"
    """)


@when(u'I attempt to log in with password "{password}"')
def attempt_login(context, password):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "login" with "$name"
        And I fill in "password" with "{}"
        And I press the element with xpath "//button[contains(string(), 'Login')]"
    """.format(password))


@when(u'I fill in "{name}" with "{value}" if present')
def fill_in_field_if_present(context, name, value):
    context.execute_steps(u"""
        When I execute the script "field = $('#field-{0}'); if (!field.length) field = $('#{0}'); if (!field.length) field = $('[name={0}]'); field.val('{1}'); field.keyup();"
    """.format(name, value))


@when(u'I clear the URL field')
def clear_url(context):
    context.execute_steps(u"""
        When I execute the script "$('a.btn-remove-url:contains(Clear)').click();"
    """)


@when(u'I open the new resource form for dataset "{name}"')
def go_to_new_resource_form(context, name):
    context.execute_steps(u"""
        When I edit the "{0}" dataset
    """.format(name))
    if context.browser.is_element_present_by_xpath("//*[contains(@class, 'btn-primary') and contains(string(), 'Next:')]"):
        # Draft dataset, proceed directly to resource form
        context.execute_steps(u"""
            When I press "Next:"
        """)
    else:
        # Existing dataset, browse to the resource form
        context.execute_steps(u"""
            When I press "Resources"
            And I press "Add new resource"
            And I take a debugging screenshot
        """)


@when(u'I fill in title with random text')
def title_random_text(context):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "title" with "Test Title {0}"
        And I fill in "name" with "test-title-{0}" if present
        And I set "last_generated_title" to "Test Title {0}"
        And I set "last_generated_name" to "test-title-{0}"
    """.format(uuid.uuid4()))


@when(u'I go to dataset page')
def go_to_dataset_page(context):
    context.execute_steps(u"""
        When I visit "/dataset"
    """)


@when(u'I go to dataset "{name}"')
def go_to_dataset(context, name):
    context.execute_steps(u"""
        When I visit "/dataset/{0}"
        And I take a debugging screenshot
    """.format(name))


@when(u'I select the "{licence_id}" licence')
def select_licence(context, licence_id):
    # Licence requires special interaction due to fancy JavaScript
    context.execute_steps(u"""
        When I execute the script "$('#field-license_id').val('{0}').trigger('change')"
    """.format(licence_id))


@when(u'I enter the resource URL "{url}"')
def enter_resource_url(context, url):
    if url != "default":
        context.execute_steps(u"""
            When I clear the URL field
            When I execute the script "$('#resource-edit [name=url]').val('{0}')"
        """.format(url))


@when(u'I fill in default dataset fields')
def fill_in_default_dataset_fields(context):
    context.execute_steps(u"""
        When I fill in title with random text
        And I fill in "notes" with "Description"
        And I fill in "version" with "1.0"
        And I fill in "author_email" with "test@me.com"
        And I select the "other-open" licence
        And I fill in "de_identified_data" with "NO" if present
    """)


@when(u'I fill in default resource fields')
def fill_in_default_resource_fields(context):
    context.execute_steps(u"""
        When I fill in "name" with "Test Resource"
        And I fill in "description" with "Test Resource Description"
        And I fill in "size" with "1024" if present
    """)


@when(u'I fill in link resource fields')
def fill_in_default_link_resource_fields(context):
    context.execute_steps(u"""
        When I enter the resource URL "https://example.com"
        And I execute the script "document.getElementById('field-format').value='HTML'"
        And I fill in "size" with "1024" if present
    """)


@when(u'I upload "{file_name}" of type "{file_format}" to resource')
def upload_file_to_resource(context, file_name, file_format):
    context.execute_steps(u"""
        When I execute the script "$('#resource-upload-button').trigger(click);"
        And I attach the file "{file_name}" to "upload"
        # Don't quote the injected string since it can have trailing spaces
        And I execute the script "document.getElementById('field-format').value='{file_format}'"
        And I fill in "size" with "1024" if present
    """.format(file_name=file_name, file_format=file_format))


@when(u'I go to organisation page')
def go_to_organisation_page(context):
    context.execute_steps(u"""
        When I visit "/organization"
    """)


# Parse a "key=value::key2=value2" parameter string and return an iterator of (key, value) pairs.
def _parse_params(param_string):
    params = {}
    for param in param_string.split("::"):
        entry = param.split("=", 1)
        params[entry[0]] = entry[1] if len(entry) > 1 else ""
    return six.iteritems(params)


def _create_dataset_from_params(context, params):
    context.execute_steps(u"""
        When I visit "/dataset/new"
        And I fill in default dataset fields
    """)
    if 'private' not in params:
        params = params + "::private=False"
    for key, value in _parse_params(params):
        if key == "name":
            # 'name' doesn't need special input, but we want to remember it
            context.execute_steps(u"""
                When I set "last_generated_name" to "{0}"
            """.format(value))

        # Don't use elif here, we still want to type 'name' as usual
        if key == "owner_org":
            # Owner org uses UUIDs as its values, so we need to rely on displayed text
            context.execute_steps(u"""
                When I select by text "{1}" from "{0}"
            """.format(key, value))
        elif key in ["private"]:
            context.execute_steps(u"""
                When I select "{1}" from "{0}"
            """.format(key, value))
        elif key == "license_id":
            context.execute_steps(u"""
                When I select the "{0}" licence
            """.format(value))
        else:
            context.execute_steps(u"""
                When I fill in "{0}" with "{1}" if present
            """.format(key, value))
    context.execute_steps(u"""
        When I take a debugging screenshot
        And I press "Add Data"
        Then I should see "Add New Resource"
    """)


@when(u'I create a dataset with key-value parameters "{params}"')
def create_dataset_from_params(context, params):
    _create_dataset_from_params(context, params)
    context.execute_steps(u"""
        When I go to dataset "$last_generated_name"
    """)


@when(u'I create a dataset and resource with key-value parameters "{params}" and "{resource_params}"')
def create_dataset_and_resource_from_params(context, params, resource_params):
    _create_dataset_from_params(context, params)
    context.execute_steps(u"""
        When I create a resource with key-value parameters "{0}"
        Then I should see "Data and Resources"
    """.format(resource_params))


# Creates a resource using default values apart from the ones specified.
# The browser should already be on the create/edit resource page.
@when(u'I create a resource with key-value parameters "{resource_params}"')
def create_resource_from_params(context, resource_params):
    context.execute_steps(u"""
        When I fill in default resource fields
        And I fill in link resource fields
    """)
    for key, value in _parse_params(resource_params):
        if key == "url":
            context.execute_steps(u"""
                When I enter the resource URL "{0}"
            """.format(value))
        elif key == "upload":
            if value == "default":
                value = "test_game_data.csv"
            context.execute_steps(u"""
                When I clear the URL field
                And I execute the script "$('#resource-upload-button').click();"
                And I attach the file "{0}" to "upload"
            """.format(value))
        elif key == "format":
            context.execute_steps(u"""
                When I execute the script "document.getElementById('field-format').value='{0}'"
            """.format(value))
        else:
            context.execute_steps(u"""
                When I fill in "{0}" with "{1}" if present
            """.format(key, value))
    context.execute_steps(u"""
        When I take a debugging screenshot
        And I press the element with xpath "//form[contains(@class, 'resource-form')]//button[contains(@class, 'btn-primary')]"
        And I take a debugging screenshot
    """)


@then(u'I should receive a base64 email at "{address}" containing "{text}"')
def should_receive_base64_email_containing_text(context, address, text):
    should_receive_base64_email_containing_texts(context, address, text, None)


@then(u'I should receive a base64 email at "{address}" containing both "{text}" and "{text2}"')
def should_receive_base64_email_containing_texts(context, address, text, text2):
    # The default behaving step does not convert base64 emails
    # Modified the default step to decode the payload from base64
    def filter_contents(mail):
        mail = email.message_from_string(mail)
        payload = mail.get_payload()
        payload += "=" * ((4 - len(payload) % 4) % 4)  # do fix the padding error issue
        payload_bytes = quopri.decodestring(payload)
        if len(payload_bytes) > 0:
            payload_bytes += b'='  # do fix the padding error issue
        if six.PY2:
            decoded_payload = payload_bytes.decode('base64')
        else:
            import base64
            decoded_payload = six.ensure_text(base64.b64decode(six.ensure_binary(payload_bytes)))
        print('Searching for', text, ' and ', text2, ' in decoded_payload: ', decoded_payload)
        return text in decoded_payload and (not text2 or text2 in decoded_payload)

    assert context.mail.user_messages(address, filter_contents)

