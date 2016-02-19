*******
Plugins
*******

To load a plugin you must add the `loadplugin` command in the configuration
file. For example::

    loadplugin pad.plugin.pyzor.PyzorPlugin

If the plugin is not located in the python path then you can also specify the
full path to the file::

    loadplugin MyCustomPlugin /home/pad/my_plugins/custom_plugin.py

Some plugins are reimplementing existing ones from SA. The full list can be
seen in :mod:`pad.plugins.__init__`::

    loadplugin Mail::SpamAssassin::Plugin::Pyzor


Available plugins
=================

.. toctree::
    :maxdepth: 1

    pad.plugins.awl
    pad.plugins.body_eval
    pad.plugins.dump_text
    pad.plugins.image_info
    pad.plugins.pdf_info
    pad.plugins.pyzor
    pad.plugins.relay_country
    pad.plugins.replace_tags
    pad.plugins.short_circuit
    pad.plugins.textcat
    pad.plugins.uri_detail
    pad.plugins.whitelist_subject


Plugin reference
================

.. toctree::

    pad.plugins


