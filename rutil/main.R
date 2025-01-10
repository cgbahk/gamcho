helpme <- function (obj) {
  tools::Rd2txt(
    utils:::.getHelpFile(as.character(help(obj))),
    path.expand("~/buffer"),
    options=list(underline_titles=FALSE),
  )

  help(obj)
}
