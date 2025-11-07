desktop_file = i18n.merge_file(
  input: 'com.github.chrplunk.desktop.in',
  output: 'com.github.chrplunk.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: datadir / 'applications'
)

appstream_file = i18n.merge_file(
  input: 'com.github.chrplunk.metainfo.xml.in',
  output: 'com.github.chrplunk.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: datadir / 'metainfo'
)

install_data('com.github.chrplunk.gschema.xml',
  install_dir: datadir / 'glib-2.0/schemas'
)
