%global crate cbindgen
%global rustflags -Clink-arg=-Wl,-z,relro,-z,now

Name:           rust-%{crate}
Version:        0.17.0
Release:        0
Summary:        A tool for generating C bindings from Rust code
License:        MPLv2.0
URL:            https://crates.io/crates/cbindgen
Source:         %{name}-%{version}.tar.bz2
BuildRequires:  cargo >= 1.30.0
BuildRequires:  rust >= 1.30.0
BuildRequires:  rust-std-static >= 1.30.0

%description
A tool for generating C/C++ bindings from Rust code.

%package     -n %{crate}
Summary:        %{summary}
License:        MPLv2.0 and MIT and BSD and (ASL 2.0 or Boost)

%description -n %{crate}
A tool for generating C/C++ bindings from Rust code.

%files       -n %{crate}
%license LICENSE
%doc contributing.md docs.md internals.md CHANGES README.md
%{_bindir}/cbindgen

%prep
%autosetup -p1 -n %{name}-%{version}/cbindgen

# To prevent error `found a virtual manifest instead of a package manifest`
rm ../vendor/cryptocorrosion/Cargo.toml
rm ../vendor/hermit/Cargo.toml
rm ../vendor/serde/Cargo.toml
rm ../vendor/serial_test/Cargo.toml

# Make nested subprojects visible for cargo
ln -s serde/serde ../vendor/serde-sl
ln -s serde/serde_derive ../vendor/serde_derive-sl
ln -s serial_test/serial_test ../vendor/serial_test-sl
ln -s serial_test/serial_test_derive ../vendor/serial_test_derive-sl
ln -s rand/rand_chacha ../vendor/rand_chacha-sl
ln -s rand/rand_core ../vendor/rand_core-sl
ln -s rand/rand_hc ../vendor/rand_hc-sl
ln -s parking_lot/lock_api ../vendor/lock_api-sl
ln -s parking_lot/core ../vendor/parking_lot_core-sl
ln -s hermit/hermit-abi ../vendor/hermit-abi-sl
ln -s winapi/i686 ../vendor/winapi-i686-pc-windows-gnu-sl
ln -s winapi/x86_64 ../vendor/winapi-x86_64-pc-windows-gnu-sl
ln -s cryptocorrosion/utils-simd/ppv-lite86 ../vendor/ppv-lite86-sl
ln -s cloudabi/rust ../vendor/cloudabi-sl

# Add `.cargo-checksum.json` for each dependency
find -L ../vendor -mindepth 2 -maxdepth 2 -type f -name Cargo.toml \
  -exec sh -c 'echo "{\"files\":{ },\"package\":\"\"}" > "$(dirname $0)/.cargo-checksum.json"' '{}' \;

# Remove dependency checksums
sed -i 's/checksum = "[^"]*"/checksum = ""/' Cargo.lock

%build
export RUSTFLAGS="%{rustflags}"
export CARGO_HOME=`pwd`/cargo-home/

cargo build --offline --frozen --release

%install
# rustflags must be exported again at install as cargo build will
# rebuild the project if it detects flags have changed (to none or other)
export RUSTFLAGS="%{rustflags}"
# install stage also requires re-export of 'cargo-home' or cargo
# will try to download source deps and rebuild
export CARGO_HOME=`pwd`/cargo-home/
# cargo install appends /bin to the path
cargo install --root=%{buildroot}%{_prefix} --path .
# remove spurious files
rm -f %{buildroot}%{_prefix}/.crates.toml
rm -f %{buildroot}%{_prefix}/.crates2.json
