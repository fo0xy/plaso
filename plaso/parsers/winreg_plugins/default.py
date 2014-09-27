#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The default Windows Registry plugin."""

from plaso.events import windows_events
from plaso.lib import utils
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class DefaultPlugin(interface.KeyPlugin):
  """Default plugin that extracts minimum information from every registry key.

  The default plugin will parse every registry key that is passed to it and
  extract minimum information, such as a list of available values and if
  possible content of those values. The timestamp used is the timestamp
  when the registry key was last modified.
  """

  NAME = 'winreg_default'
  DESCRIPTION = u'Parser for Registry data.'

  REG_TYPE = 'any'
  REG_KEYS = []

  # This is a special case, plugins normally never overwrite the priority.
  # However the default plugin should only run when all others plugins have
  # tried and failed.
  WEIGHT = 3

  def GetEntries(
      self, parser_context, key=None, registry_type=None, **unused_kwargs):
    """Returns an event object based on a Registry key name and values.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    text_dict = {}

    if key.number_of_values == 0:
      text_dict[u'Value'] = u'No values stored in key.'

    else:
      for value in key.GetValues():
        if not value.name:
          value_name = '(default)'
        else:
          value_name = u'{0:s}'.format(value.name)

        if value.data is None:
          value_string = u'[{0:s}] Empty'.format(
              value.data_type_string)
        elif value.DataIsString():
          string_decode = utils.GetUnicodeString(value.data)
          value_string = u'[{0:s}] {1:s}'.format(
              value.data_type_string, string_decode)
        elif value.DataIsInteger():
          value_string = u'[{0:s}] {1:d}'.format(
              value.data_type_string, value.data)
        elif value.DataIsMultiString():
          if type(value.data) not in (list, tuple):
            value_string = u'[{0:s}]'.format(value.data_type_string)
            # TODO: Add a flag or some sort of an anomaly alert.
          else:
            value_string = u'[{0:s}] {1:s}'.format(
                value.data_type_string, u''.join(value.data))
        else:
          value_string = u'[{0:s}]'.format(value.data_type_string)

        text_dict[value_name] = value_string

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict,
        offset=key.offset, registry_type=registry_type)
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

  # Even though the DefaultPlugin is derived from KeyPlugin it needs to
  # overwrite the Process function to make sure it is called when no other
  # plugin is available.

  def Process(
      self, parser_context, key=None, registry_type=None, **kwargs):
    """Process the key and return a generator to extract event objects.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    # Note that we should NOT call the Process function of the KeyPlugin here.
    self.GetEntries(
        parser_context, key=key, registry_type=registry_type, **kwargs)


winreg.WinRegistryParser.RegisterPlugin(DefaultPlugin)
