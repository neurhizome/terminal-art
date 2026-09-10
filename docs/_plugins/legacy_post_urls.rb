# Existing essays and bookmarks use .html; the canonical blog uses /slug/.
# Keep both reachable without rewriting the historical prose or changing URLs.
require 'cgi'

module Jekyll
  class LegacyPostUrls < Generator
    safe true
    priority :low

    def generate(site)
      site.posts.docs.each do |post|
        next unless post.url.end_with?('/')
        legacy = post.url.chomp('/') + '.html'
        target = CGI.escapeHTML(site.config['baseurl'].to_s + post.url)
        page = PageWithoutAFile.new(site, site.source, File.dirname(legacy).sub(%r{^/}, ''), File.basename(legacy))
        page.data['layout'] = nil
        page.data['sitemap'] = false
        page.content = <<~HTML
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Continue to the journal</title>
          <meta http-equiv="refresh" content="0; url=#{target}">
          <link rel="canonical" href="#{CGI.escapeHTML(site.config['url'].to_s)}#{target}">
          </head><body><p><a href="#{target}">Continue to the journal entry</a></p></body></html>
        HTML
        site.pages << page
      end
    end
  end
end
