project('chrplunk',
  version: '0.1.0',
  meson_version: '>= 0.59.0',
)

python = import('python')
i18n = import('i18n')
gnome = import('gnome')

python_installation = python.find_installation('python3')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')

pkgdatadir = datadir / meson.project_name()

install_subdir('chrplunk', install_dir: python_installation.get_install_dir())
install_data('chrplunk-app.py', install_dir: bindir, rename: 'chrplunk')

# Install language specs for GtkSourceView
install_subdir('data/language-specs',
               install_dir: datadir / 'gtksourceview-5' / 'language-specs',
               strip_directory: true)

subdir('data')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
