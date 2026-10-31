use serde::Serialize;

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum Ecosystem {
    Go,
    PyPI,
    #[serde(rename = "crates.io")]
    Crates,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct Package {
    pub ecosystem: Ecosystem,
    pub name: String,
    pub version: String,
}
