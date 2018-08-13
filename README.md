# arXiv Readability

Since its inception, arXiv’s primary distribution format has predominantly been
PDF generated from LaTeX submitted by authors. While there are no plans to move
away from LaTeX as the preferred submission format, nor to abandon PDFs, we
recognize the need to provide distribution formats that make scientific papers
more broadly usable and accessible.

- In particular, the use of mobile devices--for which PDF is unsuitable-—to
  access internet resources including arXiv content is on the rise, especially
  in developing countries.
- Adopting HTML5 also opens up the potential for authors to integrate dynamic
  content in their papers, such as embedded video or interactive elements.
- Providing an HTML5 distribution format provides a foundation for a broader
  array of enhancements and integrations by third-party developers and
  researchers that can add value for arXiv authors and readers.
- Well-formed HTML5 documents (and in particular MathML for formulae) has
  advantages over PDF for accessibility, particularly for use with screen
  readers and other assistive technology.

## Contributors
- Michael Kohlhase (Friedrich-Alexander Universität Erlangen-Nürnberg)
- Ben Firshman (arXiv-Vanity)
- Deyan Ginev (Friedrich-Alexander Universität Erlangen-Nürnberg)
- Erick Peirson (arXiv)
- Martin Lessmeister (arXiv)

## Objectives
Our top priority is to provide a high-quality service to all arXiv authors and
readers. The overarching objective of this project is to significantly improve
the usability and accessibility of arXiv papers. While providing HTML is not a
panacea, it is a first step in the right direction.

- O1: Develop a cloud-native service that provides HTML renderings from LaTeX
  source submitted to arXiv, leveraging LaTeXML.
- O2: Demonstrate the feasibility and value of the service by providing it on
  an experimental basis to arXiv authors, with links to HTML on the
  public abstract page. This will involve providing detailed guidance and
  feedback to authors about how to write LaTeX that generates high-quality
  accessible HTML.
- O3: Provided that O1 and O2 are achieved, render all arXiv papers submitted
  as LaTeX to HTML.
- O4: Provide HTML documents as API resources for third-party developers and
  researchers. A crucial component of this project is promoting experimentation
  by researchers and third-party developers, and making the results of their
  work visible to arXiv readers and at the same time providing added-value
  services to arXiv readers.

Ultimately, we would like to incorporate HTML5 as a primary distribution format
for arXiv papers, alongside PDF.

## Installing development environment

First, install Docker and pull the Engrafo image:

    $ docker pull arxivvanity/engrafo

Then run the development environment:

    $ docker-compose up

## Running tests

    $ script/test
