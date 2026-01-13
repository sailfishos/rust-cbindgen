%global rustflags -Clink-arg=-Wl,-z,relro,-z,now

Name:           rust-cbindgen
Version:        0.27.0
Release:        0
Summary:        A tool for generating C bindings from Rust code
License:        MPLv2.0
URL:            https://crates.io/crates/cbindgen
Source:         %{name}-%{version}.tar.bz2
BuildRequires:  cargo >= 1.74.0
BuildRequires:  rust >= 1.74.0
BuildRequires:  rust-std-static >= 1.74.0
Patch1:         0001-Drop-non-Linux-from-cbindgen.patch
Patch2:         0002-Remove-non-Linux-support-in-tempfile.patch
Patch3:         0003-Hardcode-versions-from-workspace.patch
Patch4:         0004-Drop-non-Linux-support-in-rustix.patch
Patch5:         0005-Drop-non-Linux-support-in-errno.patch
Patch6:         0006-Drop-non-Linux-support-in-parking-lot.patch
Patch7:         0007-Drop-non-Linux-support-in-anstyle.patch
Patch8:         0008-Fix-workspace-in-clap.patch
Patch9:         0009-Fix-workspace-in-crossbeam.patch
Patch10:        0010-Fix-workspace-in-toml.patch

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
rm ../vendor/cryptocorrosion/Cargo.toml || :
rm ../vendor/hermit/Cargo.toml || :
rm ../vendor/serde/Cargo.toml || :
rm ../vendor/serial_test/Cargo.toml || :
rm ../vendor/anstyle/Cargo.toml || :
rm ../vendor/toml/Cargo.toml || :
rm ../vendor/rust-pretty-assertions/Cargo.toml || :

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
ln -s cryptocorrosion/utils-simd/ppv-lite86 ../vendor/ppv-lite86-sl
ln -s cloudabi/rust ../vendor/cloudabi-sl
ln -s toml/crates/toml ../vendor/toml-sl
ln -s toml/crates/serde_spanned ../vendor/serde_spanned-sl
ln -s toml/crates/toml_datetime ../vendor/toml_datetime-sl
ln -s toml/crates/toml_edit ../vendor/toml_edit-sl
ln -s rust-pretty-assertions/pretty_assertions ../vendor/pretty_assertions-sl
ln -s clap/clap_builder ../vendor/clap_builder-sl
ln -s clap/clap_lex ../vendor/clap_lex-sl
ln -s anstyle/crates/anstream ../vendor/anstream-sl
ln -s anstyle/crates/anstyle ../vendor/anstyle-sl
ln -s anstyle/crates/anstyle-parse ../vendor/anstyle-parse-sl
ln -s anstyle/crates/anstyle-query ../vendor/anstyle-query-sl
ln -s anstyle/crates/anstyle-wincon ../vendor/anstyle-wincon-sl
ln -s anstyle/crates/colorchoice ../vendor/colorchoice-sl
ln -s crossbeam/crossbeam-utils ../vendor/crossbeam-utils-sl
ln -s vte/utf8parse ../vendor/utf8parse-sl

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
%ifarch %arm aarch64
cargo build -j1 --offline --frozen --target $SB2_RUST_TARGET_TRIPLE --release
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
%ifarch %arm aarch64
cargo install --root=%{buildroot}%{_prefix} --path . --target $SB2_RUST_TARGET_TRIPLE
%else
cargo install --root=%{buildroot}%{_prefix} --path .
%endif

# remove spurious files
rm -f %{buildroot}%{_prefix}/.crates.toml
rm -f %{buildroot}%{_prefix}/.crates2.json
