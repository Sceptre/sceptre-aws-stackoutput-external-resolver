# Stack Output External

Fetches the value of an output from a different Stack in the same account and
region. You can specify a optional AWS profile to connect to a different
account/region.

If the Stack whose output is being fetched is in the same StackGroup, the
basename of that Stack can be used.

Syntax:

```yaml
parameters/sceptre_user_data:
  <name>:
    !stack_output_external <full_stack_name>::<output_name>
    <optional-aws-profile-name>
```

Example:

```yaml
parameters:
  VpcIdParameter: !stack_output_external prj-network-vpc::VpcIdOutput prod
```
