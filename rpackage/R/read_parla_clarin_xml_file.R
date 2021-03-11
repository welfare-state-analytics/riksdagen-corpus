#' Read a Parla-Clarin XML file
#' 
#' @description 
#' This function reads in a Parla-Clarin XML file and converts it to an
#' R list object with class \code{parla_clarin_xml}.
#' 
#' @details 
#' For details on the Parla-Clarin XML schema, see:
#' \url{https://github.com/clarin-eric/parla-clarin}
#' 
#' @param x a file path to a Parla-Clarin XML file
#' @param ... further arguments to \code{xml2::read_xml()}.
#' 
#' @export
read_parla_clarin_xml_file <- function(x, ...){
  checkmate::assert_file_exists(x)
  pc <- xml2::read_xml(x, ...)
  pc <- xml2::as_list(pc)
  class(pc) <- "parla_clarin_xml_list"
  pc
}


