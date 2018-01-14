import pkg_resources

package_name = "remote-weather-access"

try:
    __version__ = pkg_resources.require(package_name)[0].version
except pkg_resources.DistributionNotFound:
    __version__ = "unknown"
