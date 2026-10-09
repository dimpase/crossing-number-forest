<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:f="http://www.forester-notes.org" exclude-result-prefixes="f">
  <xsl:import href="../theme/default.xsl"/>
  <!-- Keep canonical tags visible wherever a note is cited, including rich labels. -->
  <xsl:template match="f:link[@type='local' and @display-uri]">
    <a class="concept-link" href="{@href}" title="{@title}" data-note-tag="{@display-uri}">
      <xsl:apply-templates/>
      <xsl:text> </xsl:text>
      <span class="reference-tag">[<xsl:value-of select="@display-uri"/>]</span>
    </a>
  </xsl:template>
  <xsl:template match="text()[ancestor::f:link[1][@type='local' and @display-uri]]">
    <xsl:value-of select="."/>
  </xsl:template>

  <!-- Status precedes the mathematics; provenance and dependencies follow it. -->
  <xsl:template match="f:mainmatter">
    <xsl:for-each select="../f:frontmatter/f:meta[@name='status']">
      <p class="note-status">Status: <span class="status status-{.}"><xsl:value-of select="."/></span></p>
    </xsl:for-each>
    <xsl:apply-imports/>
    <xsl:if test="../f:frontmatter/f:meta[@name='provenance']">
      <dl class="note-facts">
        <xsl:for-each select="../f:frontmatter/f:meta[@name='dependencies']">
          <dt>Proof dependencies</dt><dd><xsl:apply-templates/></dd>
        </xsl:for-each>
        <xsl:for-each select="../f:frontmatter/f:meta[@name='provenance']">
          <dt>Provenance</dt><dd><xsl:apply-templates/></dd>
        </xsl:for-each>
      </dl>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
