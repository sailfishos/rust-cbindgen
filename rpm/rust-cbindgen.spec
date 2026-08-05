%global rustflags -Clink-arg=-Wl,-z,relro,-z,now

%if ! %{defined _cargo_offline}
%global _cargo_offline %{nil}
%endif

Name:           rust-cbindgen
Version:        0.27.0
Release:        0
Summary:        A tool for generating C bindings from Rust code
License:        MPLv2.0
URL:            https://github.com/sailfishos/rust-cbindgen
Source0:        %{name}-%{version}.tar.bz2
Source1:        vendor.tar.zst
Source2:        cargo_config
BuildRequires:  cargo >= 1.74.0
BuildRequires:  rust >= 1.74.0
BuildRequires:  rust-std-static >= 1.74.0

%description
A tool for generating C/C++ bindings from Rust code.

%package     -n cbindgen
Summary:        %{summary}
License:        MPLv2.0 and MIT and BSD and (ASL 2.0 or Boost)

%description -n cbindgen
A tool for generating C/C++ bindings from Rust code.

%prep
%autosetup -a1 -n %{name}-%{version}/cbindgen

%if 0%{?_obs_build_project:1}
install -D -m 644 %{SOURCE2} .cargo/config
%endif

%build
# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 and x86_64 so this is how it knows differently. Not needed
# for native x86 and x86_64 builds
%ifarch %arm
export SB2_RUST_TARGET_TRIPLE=armv7-unknown-linux-gnueabihf
%endif
%ifarch aarch64
export SB2_RUST_TARGET_TRIPLE=aarch64-unknown-linux-gnu
%endif
# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
%ifnarch %{ix86} x86_64
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
%endif

export RUSTFLAGS="%{rustflags}"
export CARGO_HOME=`pwd`/cargo-home/

export CARGO_OFFLINE="%{_cargo_offline}"

# Forcing cargo builds to use a single core in order to make it build more
# reliably. Let's revisit when we upgrade rust. JB#53588
%ifarch %arm aarch64
cargo build -j1 $CARGO_OFFLINE --locked --target $SB2_RUST_TARGET_TRIPLE --release
%else
cargo build -j1 $CARGO_OFFLINE --locked --release
%endif

%install
# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 or x86_64 so this is how it knows differently. Not needed
# for native x86 and x86_64 builds
%ifarch %arm
export SB2_RUST_TARGET_TRIPLE=armv7-unknown-linux-gnueabihf
%endif
%ifarch aarch64
export SB2_RUST_TARGET_TRIPLE=aarch64-unknown-linux-gnu
%endif
# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
%ifnarch %{ix86} x86_64
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
cargo install --locked --root=%{buildroot}%{_prefix} --path . --target $SB2_RUST_TARGET_TRIPLE
%else
cargo install --locked --root=%{buildroot}%{_prefix} --path .
%endif

# remove spurious files
rm -f %{buildroot}%{_prefix}/.crates.toml
rm -f %{buildroot}%{_prefix}/.crates2.json

%files -n cbindgen
%license LICENSE
%doc contributing.md docs.md internals.md CHANGES README.md
%{_bindir}/cbindgen
