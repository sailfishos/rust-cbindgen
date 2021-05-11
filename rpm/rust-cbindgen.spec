%global rustflags -Clink-arg=-Wl,-z,relro,-z,now

Name:           rust-cbindgen
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

%package     -n cbindgen
Summary:        %{summary}
License:        MPLv2.0 and MIT and BSD and (ASL 2.0 or Boost)

%description -n cbindgen
A tool for generating C/C++ bindings from Rust code.

%files       -n cbindgen
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
# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 so this is how it knows differently. Not needed
# for native x86 builds
%ifarch %arm
export SB2_RUST_TARGET_TRIPLE=armv7-unknown-linux-gnueabihf
%endif
%ifarch aarch64
export SB2_RUST_TARGET_TRIPLE=aarch64-unknown-linux-gnu
%endif
# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
%ifnarch %{ix86}
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
%endif

export RUSTFLAGS="%{rustflags}"
export CARGO_HOME=`pwd`/cargo-home/

# Forcing cargo builds to use a single core in order to make it build more
# reliably. Let's revisit when we upgrade rust. JB#53588

%ifarch %arm
cargo build -j1 --offline --frozen --target armv7-unknown-linux-gnueabihf --release
%else
cargo build -j1 --offline --frozen --release
%endif

%install
# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 so this is how it knows differently. Not needed
# for native x86 builds
%ifarch %arm
export SB2_RUST_TARGET_TRIPLE=armv7-unknown-linux-gnueabihf
%endif
%ifarch aarch64
export SB2_RUST_TARGET_TRIPLE=aarch64-unknown-linux-gnu
%endif
# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
%ifnarch %{ix86}
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
%endif

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
