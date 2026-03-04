class TronTwitter < Formula
  include Language::Python::Virtualenv

  desc "Twitter/X CLI for Tron agent"
  homepage "https://github.com/mhismail3/tron-twitter"
  url "https://github.com/mhismail3/tron-twitter/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.11"

  # Resource stanzas generated via: brew update-python-resources tron-twitter
  # Run this after first release to populate dependency resources.

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tron-twitter", "--version"
  end
end
