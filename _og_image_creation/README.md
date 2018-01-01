## Generating OpenGraph Images for PlanScore.org

This folder contains state-specific Open Graph images.

Updating these images requires three files:

1. `planscore_opengraph_generator.ai` in this folder
2. `VariableImporter.jsx` in this folder
3. A data CSV exported from the "final_AI" tab in this Google Sheet: https://docs.google.com/spreadsheets/d/17t_l0yRl7wFTDya3RiQeZNhA6MBI8daqYHvwewd-3F8/edit#gid=1767310777
4. PlanScoreOG.aia, a presaved AI Action for batch export.

For background, see [this Adobe forum post](https://forums.adobe.com/thread/1726468) and [this Github repo](https://github.com/Silly-V/Adobe-Illustrator/blob/master/Variable%20Importer/VariableImporter.jsx).

The Illustrator file contains objects named in the layer palette to match the names of the columns in the "final_AI" tab.

Here's how to update the graphics:

1. Make whatever design changes you want in the AI file.
2. Make text changes or formula updates in Sheets and export a CSV.
3. In Illustrator, use File>Scripts>Other Script (Command-F12) and select VariableImporter.jsx to use the Variable Importer.
4. In the resulting dialog, choose your CSV as your data source, then:
	* Under Options>Dataset Names, click Assign
	* For `Field 1` choose "Custom Text" and enter "OG"
	* For `Field 2` choose "Dash"
	* For `Field 3` choose "SLUG". 
	* Set all other Fields to "Nothing". This will ensure Illustrator names each record with the state slug we'll use later to name the output files.
	* Import the data. You'll get a warning about overwriting existing data. That's fine.
5. You can use the Window>Variables to cycle through and see the data in place to verify.
6. Using the Actions panel, use the panel menu in upper right to select "Load Actions" and choose "PlanScoreOG.aia" (you need to do this only the first time). This loads the "SaveOG" settings for batch export. 
7. Trash the existing "OG-" images in "PlanScore/WEBSITE_OUTPUT/images/" to make way for the new images.
8. In Actions, do "Batch" and choose "SaveOG". Select "Override Actions Export Commands" and choose "PlanScore/WEBSITE_OUTPUT/images/" folder as destination. Under File Name, select "Data Set Name". Click OK. This will generate all the properly named OG images.

Note that Illustrator insists on appending `-01` to the end of each filename. There isn't a readily obvious way to avoid that, so we just accommodate it in our HTML source reference.



