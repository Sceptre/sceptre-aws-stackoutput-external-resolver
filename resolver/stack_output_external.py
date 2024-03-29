# -*- coding: utf-8 -*-

import abc
import six
import logging
import shlex

from botocore.exceptions import ClientError

from sceptre.resolvers import Resolver
from sceptre.exceptions import DependencyStackMissingOutputError
from sceptre.exceptions import StackDoesNotExistError

TEMPLATE_EXTENSION = ".yaml"


@six.add_metaclass(abc.ABCMeta)
class StackOutputBase(Resolver):
    """
    A abstract base class which provides methods for getting Stack outputs.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(StackOutputBase, self).__init__(*args, **kwargs)

    def _get_output_value(self, stack_name, output_key, profile=None, region=None):
        """
        Attempts to get the Stack output named by ``output_key``

        :param stack_name: Name of the Stack to collect output for.
        :type stack_name: str
        :param output_key: The name of the Stack output in which to return.
        :type output_key: str
        :returns: Stack output value.
        :rtype: str
        :raises: sceptre.exceptions.DependencyStackMissingOutputError
        """
        outputs = self._get_stack_outputs(stack_name, profile, region)

        try:
            return outputs[output_key]
        except KeyError:
            raise DependencyStackMissingOutputError(
                "The Stack '{0}' does not have an output named '{1}'".format(
                    stack_name, output_key
                )
            )

    def _get_stack_outputs(self, stack_name, profile=None, region=None):
        """
        Communicates with AWS CloudFormation to fetch outputs from a specific
        Stack.

        :param stack_name: Name of the Stack to collect output for.
        :type stack_name: str
        :returns: A formatted version of the Stack outputs.
        :rtype: dict
        :raises: sceptre.stack.DependencyStackNotLaunchedException
        """
        self.logger.debug("Collecting outputs from '{0}'...".format(
            stack_name
        ))
        connection_manager = self.stack.connection_manager

        try:
            response = connection_manager.call(
                service="cloudformation",
                command="describe_stacks",
                kwargs={"StackName": stack_name},
                profile=profile,
                region=region,
                stack_name=stack_name
            )
        except ClientError as e:
            if "does not exist" in e.response["Error"]["Message"]:
                raise StackDoesNotExistError(e.response["Error"]["Message"])
            else:
                raise e
        else:
            outputs = response["Stacks"][0].get("Outputs", {})

        self.logger.debug("Outputs: {0}".format(outputs))

        formatted_outputs = dict(
            (output["OutputKey"], output["OutputValue"])
            for output in outputs
        )

        return formatted_outputs


class StackOutputExternal(StackOutputBase):
    """
    Resolver for retrieving the value of an output of any Stack within the
    current Sceptre stack_group's account and region.

    :param argument: The Stack name and output name to get.
    :type argument: str in the format ``"<full stack name>::<output key>"``
    """

    def __init__(self, *args, **kwargs):
        super(StackOutputExternal, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves the value of CloudFormation output of the external Stack

        :returns: The value of the Stack output.
        :rtype: str
        """
        self.logger.debug(
            "Resolving external Stack output: {0}".format(self.argument)
        )

        profile = None
        arguments = shlex.split(self.argument)

        stack_argument = arguments[0]
        if len(arguments) > 1:
            profile = arguments[1]

        dependency_stack_name, output_key = stack_argument.split("::")
        return self._get_output_value(
            dependency_stack_name, output_key, profile
        )
