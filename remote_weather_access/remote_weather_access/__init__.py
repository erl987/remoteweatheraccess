import pkg_resources

package_name = "remote-weather-access"
__version__ = pkg_resources.require(package_name)[0].version
