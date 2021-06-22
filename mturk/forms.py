from django import forms


class CreateHITForm(forms.Form):
    use_sandbox = forms.BooleanField(
        initial=True,
        required=False,
        label='Use MTurk Sandbox (for development and testing)',
        help_text="""If this box is checked, your HIT will not be published to the MTurk live site, but rather
          to the MTurk Sandbox, so you can test how it will look to MTurk workers.""",
    )
