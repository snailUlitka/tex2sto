-- Apply explicit tex2sto semantic styles before the DOCX writer runs.

function Para(element)
  local text = pandoc.utils.stringify(element)
  local style = "Tex2Sto Body"
  if text:match("^Рисунок%s") then
    style = "Tex2Sto Figure Caption"
  elseif text:match("^Таблица%s") then
    style = "Tex2Sto Table Caption"
  end
  return pandoc.Div({ element }, pandoc.Attr("", {}, { ["custom-style"] = style }))
end

function Header(element)
  element.attr.attributes["custom-style"] = "Tex2Sto Heading " .. tostring(element.level)
  return element
end

function CodeBlock(element)
  element.attr.attributes["custom-style"] = "Tex2Sto Code"
  return element
end
